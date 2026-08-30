"""In-memory Supabase Mock Client — enables complete demo and execution without external DB."""

import json
import os
import uuid
import copy
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MockQueryResult:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class MockQueryBuilder:
    def __init__(self, table_name: str, db: "MockSupabaseClient"):
        self.table_name = table_name
        self.db = db
        self._select_cols = "*"
        self._count_mode = None
        self._filters = []
        self._order_col = None
        self._order_desc = False
        self._range_start = 0
        self._range_end = None
        self._is_single = False
        self._pending_insert = None
        self._pending_update = None
        self._pending_delete = False

    def select(self, columns: str = "*", count: str = None):
        self._select_cols = columns
        self._count_mode = count
        return self

    def insert(self, data):
        self._pending_insert = data
        return self

    def update(self, data: dict):
        self._pending_update = data
        return self

    def delete(self):
        self._pending_delete = True
        return self

    def eq(self, column: str, value):
        self._filters.append(("eq", column, value))
        return self

    def in_(self, column: str, values: list):
        self._filters.append(("in", column, set(values)))
        return self

    def order(self, column: str, desc: bool = False):
        self._order_col = column
        self._order_desc = desc
        return self

    def range(self, start: int, end: int):
        self._range_start = start
        self._range_end = end
        return self

    def limit(self, count: int):
        self._range_start = 0
        self._range_end = count - 1 if count > 0 else 0
        return self

    def single(self):
        self._is_single = True
        return self

    def execute(self) -> MockQueryResult:
        table = self.db.get_table(self.table_name)

        # Handle INSERT
        if self._pending_insert is not None:
            items = self._pending_insert if isinstance(self._pending_insert, list) else [self._pending_insert]
            inserted = []
            now_iso = datetime.utcnow().isoformat()
            for item in items:
                row = copy.deepcopy(item)
                if "id" not in row:
                    row["id"] = str(uuid.uuid4())
                if "created_at" not in row:
                    row["created_at"] = now_iso
                if "updated_at" not in row and self.table_name in ("transactions", "recovery_cases"):
                    row["updated_at"] = now_iso
                table.append(row)
                inserted.append(row)
            return MockQueryResult(inserted, len(inserted))

        # Handle UPDATE
        if self._pending_update is not None:
            updated = []
            now_iso = datetime.utcnow().isoformat()
            for row in table:
                if self._match_filters(row):
                    for k, v in self._pending_update.items():
                        row[k] = v
                    if "updated_at" in row or self.table_name in ("transactions", "recovery_cases"):
                        row["updated_at"] = now_iso
                    updated.append(copy.deepcopy(row))
            return MockQueryResult(updated, len(updated))

        # Handle DELETE
        if self._pending_delete:
            remaining = [row for row in table if not self._match_filters(row)]
            deleted_count = len(table) - len(remaining)
            self.db.set_table(self.table_name, remaining)
            return MockQueryResult([], deleted_count)

        # Handle SELECT
        rows = [row for row in table if self._match_filters(row)]
        exact_count = len(rows)

        # Sort
        if self._order_col:
            rows.sort(
                key=lambda x: str(x.get(self._order_col, "")),
                reverse=self._order_desc,
            )

        # Range / pagination
        if self._range_end is not None:
            rows = rows[self._range_start : self._range_end + 1]
        elif self._range_start > 0:
            rows = rows[self._range_start :]

        # Build join objects if nested select is requested (e.g. transactions!inner(...), customers!inner(...))
        result_rows = []
        for r in rows:
            row_copy = copy.deepcopy(r)
            if self.table_name == "recovery_cases":
                # Join transaction
                txn = self.db.find_one("transactions", "id", r.get("transaction_id"))
                if txn:
                    row_copy["transactions"] = {
                        "amount": txn.get("amount", 0),
                        "payment_method": txn.get("payment_method", ""),
                        "failure_reason": txn.get("failure_reason", ""),
                        "status": txn.get("status", ""),
                        "retry_count": txn.get("retry_count", 0),
                    }
                # Join customer
                cust = self.db.find_one("customers", "id", r.get("customer_id"))
                if cust:
                    row_copy["customers"] = {
                        "name": cust.get("name", "Unknown"),
                        "email": cust.get("email", ""),
                        "previous_success_rate": cust.get("previous_success_rate", 0.0),
                    }
            result_rows.append(row_copy)

        if self._is_single:
            if not result_rows:
                raise ValueError(f"No row found in {self.table_name} matching criteria")
            return MockQueryResult(result_rows[0], exact_count)

        return MockQueryResult(result_rows, exact_count)

    def _match_filters(self, row: dict) -> bool:
        for ftype, col, val in self._filters:
            row_val = row.get(col)
            if ftype == "eq":
                if str(row_val) != str(val):
                    return False
            elif ftype == "in":
                if str(row_val) not in {str(v) for v in val}:
                    return False
        return True


class MockSupabaseClient:
    """Complete in-memory database that mimics Supabase postgrest tables."""

    def __init__(self):
        global _global_mock_client
        _global_mock_client = self
        self._tables: dict[str, list[dict]] = {
            "customers": [],
            "transactions": [],
            "recovery_cases": [],
            "recovery_actions": [],
            "audit_logs": [],
        }
        self._initialize_demo_data()

    def table(self, table_name: str) -> MockQueryBuilder:
        return MockQueryBuilder(table_name, self)

    def get_table(self, table_name: str) -> list[dict]:
        return self._tables.setdefault(table_name, [])

    def set_table(self, table_name: str, rows: list[dict]):
        self._tables[table_name] = rows

    def find_one(self, table_name: str, col: str, val) -> dict | None:
        for row in self.get_table(table_name):
            if str(row.get(col)) == str(val):
                return row
        return None

    def _initialize_demo_data(self):
        """Populate realistic demo data from synthetic dataset or generator."""
        logger.info("[Mock Database] Initializing in-memory tables...")
        dataset = None
        data_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_data.json"))
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    dataset = json.load(f)
            except Exception:
                dataset = None

        if not dataset:
            from scripts.generate_data import generate_synthetic_dataset
            dataset = generate_synthetic_dataset(num_customers=120, num_transactions=400)

        # 1. Customers
        customer_id_map = {}
        for cust in dataset["customers"]:
            real_id = str(uuid.uuid4())
            customer_id_map[cust["temp_id"]] = real_id
            self._tables["customers"].append({
                "id": real_id,
                "name": cust["name"],
                "email": cust["email"],
                "phone": cust["phone"],
                "previous_success_rate": cust["previous_success_rate"],
                "created_at": (datetime.utcnow() - timedelta(days=25)).isoformat(),
            })

        # 2. Transactions
        failed_txns = []
        for txn in dataset["transactions"]:
            txn_id = str(uuid.uuid4())
            cust_id = customer_id_map.get(txn.get("temp_customer_id"), self._tables["customers"][0]["id"])
            row = {
                "id": txn_id,
                "customer_id": cust_id,
                "amount": txn["amount"],
                "currency": "INR",
                "payment_method": txn["payment_method"],
                "status": txn["status"],
                "failure_reason": txn.get("failure_reason"),
                "retry_count": txn.get("retry_count", 0),
                "created_at": txn["created_at"],
                "updated_at": txn["created_at"],
            }
            self._tables["transactions"].append(row)
            if row["status"] == "FAILED":
                failed_txns.append(row)

        # 3. Create initial recovery cases, actions, and audit logs
        # Process first 60 failed transactions so the dashboard has rich initial analytics!
        from app.services.gemini_service import _fallback_analysis

        for txn in failed_txns[:60]:
            case_id = str(uuid.uuid4())
            amount = txn["amount"]
            reason = txn.get("failure_reason") or "BANK_TIMEOUT"
            retry_count = txn.get("retry_count", 0)
            cust = self.find_one("customers", "id", txn["customer_id"]) or {}
            success_rate = cust.get("previous_success_rate", 0.5)

            # Analyze
            analysis = _fallback_analysis(reason, retry_count, success_rate)
            # Direct policy evaluation for initialization
            if retry_count >= 3:
                pol_status = "STOPPED_BY_POLICY"
                pol_reason = f"Retry count ({retry_count}) has reached maximum (3). No further retries allowed."
            elif amount >= 50000:
                pol_status = "REQUIRES_HUMAN_APPROVAL"
                pol_reason = f"Transaction amount INR {amount:,.2f} exceeds high-value threshold (INR 50,000.00). Requires human approval."
            elif analysis.recommended_action == "STOP_RECOVERY":
                pol_status = "APPROVED"
                pol_reason = "AI recommends stopping recovery. Policy confirms."
            else:
                pol_status = "APPROVED"
                pol_reason = f"Action '{analysis.recommended_action}' is within policy limits."

            # Determine status & outcome
            if pol_status == "REQUIRES_HUMAN_APPROVAL":
                status = "REQUIRES_HUMAN_APPROVAL"
                rec_amount = 0.0
                action_type = analysis.recommended_action
            elif pol_status in ("STOPPED_BY_POLICY", "BLOCKED"):
                status = "STOPPED_BY_POLICY"
                rec_amount = 0.0
                action_type = "STOP_RECOVERY"
            elif analysis.recommended_action == "STOP_RECOVERY":
                status = "STOPPED"
                rec_amount = 0.0
                action_type = "STOP_RECOVERY"
            elif analysis.recommended_action == "RETRY_LATER":
                is_rec = success_rate > 0.4 and retry_count < 2
                status = "RECOVERED" if is_rec else "RECOVERY_FAILED"
                rec_amount = amount if is_rec else 0.0
                action_type = "RETRY_LATER"
            else:
                is_rec = success_rate > 0.5
                status = "RECOVERED" if is_rec else "IN_PROGRESS"
                rec_amount = amount if is_rec else 0.0
                action_type = analysis.recommended_action

            case_row = {
                "id": case_id,
                "transaction_id": txn["id"],
                "customer_id": txn["customer_id"],
                "amount_at_risk": amount,
                "diagnosis": analysis.diagnosis,
                "ai_recommendation": analysis.recommended_action,
                "selected_action": action_type,
                "status": status,
                "recovered_amount": rec_amount,
                "created_at": txn["created_at"],
                "updated_at": txn["updated_at"],
            }
            self._tables["recovery_cases"].append(case_row)

            # Action entry
            self._tables["recovery_actions"].append({
                "id": str(uuid.uuid4()),
                "recovery_case_id": case_id,
                "action_type": action_type,
                "execution_status": "COMPLETED" if status == "RECOVERED" else "PENDING",
                "razorpay_payment_link_id": f"plink_mock_{case_id[:8]}" if "PAYMENT_LINK" in action_type else None,
                "details": {
                    "short_url": f"https://rzp.io/i/mock_{case_id[:8]}",
                    "reason": pol_reason,
                    "is_mock": True,
                },
                "created_at": txn["created_at"],
            })

            # Audit trail
            self._tables["audit_logs"].extend([
                {
                    "id": str(uuid.uuid4()),
                    "recovery_case_id": case_id,
                    "component": "Revenue Loss Detector",
                    "event_type": "CASE_CREATED",
                    "message": f"Failed payment detected. Recovery case created. Amount at risk: INR {amount:,.2f}",
                    "metadata": {"amount": amount},
                    "created_at": txn["created_at"],
                },
                {
                    "id": str(uuid.uuid4()),
                    "recovery_case_id": case_id,
                    "component": "Gemini AI",
                    "event_type": "ANALYSIS_COMPLETE",
                    "message": f"Diagnosis: {analysis.diagnosis}",
                    "metadata": {"recommended_action": analysis.recommended_action},
                    "created_at": txn["created_at"],
                },
                {
                    "id": str(uuid.uuid4()),
                    "recovery_case_id": case_id,
                    "component": "Policy Engine",
                    "event_type": pol_status,
                    "message": pol_reason,
                    "metadata": {"policy_status": pol_status},
                    "created_at": txn["created_at"],
                },
            ])

        logger.info(
            f"[Mock Database] Ready with {len(self._tables['customers'])} customers, "
            f"{len(self._tables['transactions'])} transactions, "
            f"{len(self._tables['recovery_cases'])} recovery cases."
        )


_global_mock_client: MockSupabaseClient | None = None

def get_mock_supabase() -> MockSupabaseClient:
    global _global_mock_client
    if _global_mock_client is None:
        _global_mock_client = MockSupabaseClient()
    return _global_mock_client
