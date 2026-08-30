from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


# --- Enums ---

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class FailureReason(str, Enum):
    BANK_TIMEOUT = "BANK_TIMEOUT"
    UPI_TIMEOUT = "UPI_TIMEOUT"
    CARD_DECLINED = "CARD_DECLINED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "CARD"
    NETBANKING = "NETBANKING"
    WALLET = "WALLET"


class RecoveryStatus(str, Enum):
    OPEN = "OPEN"
    ANALYZING = "ANALYZING"
    ACTION_PENDING = "ACTION_PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RECOVERED = "RECOVERED"
    RECOVERY_FAILED = "RECOVERY_FAILED"
    STOPPED = "STOPPED"
    STOPPED_BY_POLICY = "STOPPED_BY_POLICY"
    REQUIRES_HUMAN_APPROVAL = "REQUIRES_HUMAN_APPROVAL"
    ESCALATED = "ESCALATED"


class ActionType(str, Enum):
    RETRY_LATER = "RETRY_LATER"
    CREATE_PAYMENT_LINK = "CREATE_PAYMENT_LINK"
    RECOMMEND_ALTERNATIVE_METHOD = "RECOMMEND_ALTERNATIVE_METHOD"
    STOP_RECOVERY = "STOP_RECOVERY"
    ESCALATE = "ESCALATE"


class PolicyStatus(str, Enum):
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    REQUIRES_HUMAN_APPROVAL = "REQUIRES_HUMAN_APPROVAL"
    STOPPED_BY_POLICY = "STOPPED_BY_POLICY"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


# --- Request / Response Models ---

class CustomerOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    previous_success_rate: float = 0.0
    created_at: Optional[str] = None


class TransactionOut(BaseModel):
    id: str
    customer_id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    payment_method: str
    status: str
    failure_reason: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    customer: Optional[CustomerOut] = None


class RecoveryCaseOut(BaseModel):
    id: str
    transaction_id: str
    customer_id: str
    amount_at_risk: float
    diagnosis: Optional[str] = None
    ai_recommendation: Optional[str] = None
    selected_action: Optional[str] = None
    status: str
    recovered_amount: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    transaction: Optional[TransactionOut] = None
    customer: Optional[CustomerOut] = None


class RecoveryActionOut(BaseModel):
    id: str
    recovery_case_id: str
    action_type: str
    execution_status: str
    razorpay_payment_link_id: Optional[str] = None
    details: Optional[dict] = None
    created_at: Optional[str] = None


class AuditLogOut(BaseModel):
    id: str
    recovery_case_id: Optional[str] = None
    component: str
    event_type: str
    message: str
    metadata: Optional[dict] = None
    created_at: Optional[str] = None


# --- AI Models ---

class GeminiAnalysis(BaseModel):
    diagnosis: str
    confidence: str = Field(pattern=r"^(high|medium|low)$")
    recommended_action: str
    reason: str
    customer_message: Optional[str] = None


class PolicyDecision(BaseModel):
    status: str
    reason: str


# --- API Request Models ---

class FailedPaymentEvent(BaseModel):
    customer_id: str
    amount: float
    currency: str = "INR"
    payment_method: str
    failure_reason: str


class DemoScenarioRequest(BaseModel):
    scenario: int = Field(ge=1, le=4)


class CustomScenarioRequest(BaseModel):
    amount: float = Field(gt=0, default=2499.0)
    payment_method: str = Field(default="UPI")
    failure_reason: str = Field(default="BANK_TIMEOUT")
    customer_success_rate: float = Field(ge=0.0, le=1.0, default=0.8)
    retry_count: int = Field(ge=0, le=10, default=0)
    customer_name: Optional[str] = "Demo User"


class PaymentLinkRequest(BaseModel):
    recovery_case_id: str
    amount: float
    customer_name: str
    customer_email: str
    description: str = "Payment Recovery"


class PaymentVerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_payment_link_id: str
    razorpay_signature: Optional[str] = None
    recovery_case_id: str


# --- Dashboard Models ---

class DashboardMetrics(BaseModel):
    total_revenue_at_risk: float
    total_revenue_recovered: float
    recovery_rate: float
    active_recovery_cases: int
    cases_stopped_by_policy: int
    total_cases: int
    total_transactions: int
    total_failed: int


class AnalyticsData(BaseModel):
    cases_by_status: list[dict]
    failure_reason_distribution: list[dict]
    recovery_action_distribution: list[dict]
    recovery_timeline: list[dict]


# --- Batch Simulation ---

class BatchSimulationResult(BaseModel):
    total_processed: int
    total_revenue_at_risk: float
    total_recovered: float
    recovery_rate: float
    cases_stopped: int
    payment_links_created: int
    retries_performed: int
    baseline_recovery_rate: float
    reva_recovery_rate: float
    cases: list[dict] = []


# --- Convenient Aliases ---
Customer = CustomerOut
Transaction = TransactionOut
RecoveryCase = RecoveryCaseOut
RecoveryAction = RecoveryActionOut
AuditLog = AuditLogOut
RecoveryActionType = ActionType
AnalyzeRequest = dict
ExecuteActionRequest = dict
ApproveActionRequest = dict
CaseListResponse = dict
CaseDetailResponse = dict
