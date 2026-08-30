"""Synthetic data generator — seeds Supabase with realistic demo data."""

import random
import uuid
from datetime import datetime, timedelta
from app.database.supabase_client import get_supabase

# Indian first and last names
FIRST_NAMES = [
    "Aarav", "Aditi", "Arjun", "Ananya", "Bhavesh", "Chitra", "Deepak", "Divya",
    "Gaurav", "Ishaan", "Jaya", "Karan", "Lakshmi", "Manish", "Neha", "Omkar",
    "Priya", "Rahul", "Sneha", "Tanvi", "Uday", "Varun", "Yash", "Zara",
    "Aditya", "Meera", "Rohan", "Sakshi", "Vikram", "Pooja", "Nikhil", "Kavya",
    "Siddharth", "Riya", "Amit", "Anushka", "Harsh", "Swati", "Kunal", "Nisha",
    "Rajesh", "Sunita", "Mohit", "Pallavi", "Ankur", "Shweta", "Vivek", "Anjali",
    "Sanjay", "Rekha"
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Reddy", "Joshi", "Verma",
    "Iyer", "Nair", "Desai", "Mehta", "Agarwal", "Bhat", "Chopra", "Das",
    "Kulkarni", "Menon", "Rao", "Sinha", "Tiwari", "Banerjee", "Chatterjee",
    "Mukherjee", "Pillai", "Saxena", "Kapoor", "Malhotra", "Mishra", "Pandey"
]

PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET"]
FAILURE_REASONS = ["BANK_TIMEOUT", "UPI_TIMEOUT", "CARD_DECLINED", "INSUFFICIENT_BALANCE", "TECHNICAL_FAILURE"]

# Realistic transaction amounts in INR
AMOUNTS = [
    99, 149, 199, 249, 299, 399, 499, 599, 699, 799, 899, 999,
    1199, 1499, 1999, 2499, 2999, 3499, 3999, 4999,
    5999, 7499, 8999, 9999, 12999, 14999, 19999, 24999,
    29999, 34999, 39999, 49999, 54999, 59999, 74999, 99999
]


def generate_customers(count: int = 120) -> list[dict]:
    """Generate realistic customer data."""
    customers = []
    used_emails = set()

    for _ in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"

        # Generate unique email
        email_base = f"{first.lower()}.{last.lower()}"
        email = f"{email_base}@{'gmail.com' if random.random() > 0.3 else 'outlook.com'}"
        suffix = 1
        while email in used_emails:
            email = f"{email_base}{suffix}@gmail.com"
            suffix += 1
        used_emails.add(email)

        phone = f"+91{random.randint(7000000000, 9999999999)}"
        success_rate = round(random.uniform(0.2, 0.98), 2)

        customers.append({
            "name": name,
            "email": email,
            "phone": phone,
            "previous_success_rate": success_rate,
        })

    return customers


def generate_transactions(customer_ids: list[str], count: int = 400) -> list[dict]:
    """Generate a mix of successful and failed transactions."""
    transactions = []
    now = datetime.utcnow()

    for i in range(count):
        customer_id = random.choice(customer_ids)
        amount = random.choice(AMOUNTS)
        method = random.choice(PAYMENT_METHODS)
        created = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

        # ~40% failure rate to generate enough recovery cases
        if random.random() < 0.40:
            status = "FAILED"
            failure_reason = random.choice(FAILURE_REASONS)
            # UPI timeout more common with UPI, card declined with cards
            if method == "UPI" and random.random() > 0.4:
                failure_reason = "UPI_TIMEOUT"
            elif method == "CARD" and random.random() > 0.5:
                failure_reason = "CARD_DECLINED"
        else:
            status = "SUCCESS"
            failure_reason = None

        retry_count = 0
        if status == "FAILED":
            retry_count = random.choices([0, 1, 2, 3, 4], weights=[40, 30, 15, 10, 5])[0]

        transactions.append({
            "customer_id": customer_id,
            "amount": amount,
            "currency": "INR",
            "payment_method": method,
            "status": status,
            "failure_reason": failure_reason,
            "retry_count": retry_count,
            "created_at": created.isoformat(),
            "updated_at": created.isoformat(),
        })

    return transactions


def seed_database():
    """Main seed function — populates Supabase with demo data."""
    db = get_supabase()

    print("[INFO] Seeding REVA database...")

    # Check if data already exists
    existing = db.table("customers").select("id", count="exact").execute()
    if existing.count and existing.count > 0:
        print(f"[WARN] Database already has {existing.count} customers. Skipping seed.")
        print("       To re-seed, truncate tables first.")
        return

    # 1. Generate and insert customers
    print("[INFO] Generating customers...")
    customers = generate_customers(120)

    # Insert in batches of 50
    inserted_customers = []
    for i in range(0, len(customers), 50):
        batch = customers[i:i+50]
        result = db.table("customers").insert(batch).execute()
        inserted_customers.extend(result.data)
    print(f"   [+] {len(inserted_customers)} customers created")

    customer_ids = [c["id"] for c in inserted_customers]

    # 2. Generate and insert transactions
    print("[INFO] Generating transactions...")
    transactions = generate_transactions(customer_ids, 400)

    inserted_txns = []
    for i in range(0, len(transactions), 50):
        batch = transactions[i:i+50]
        result = db.table("transactions").insert(batch).execute()
        inserted_txns.extend(result.data)

    failed_count = sum(1 for t in inserted_txns if t["status"] == "FAILED")
    success_count = len(inserted_txns) - failed_count
    print(f"   [+] {len(inserted_txns)} transactions created ({success_count} success, {failed_count} failed)")

    total_amount = sum(t["amount"] for t in inserted_txns if t["status"] == "FAILED")
    print(f"   Total revenue at risk: INR {total_amount:,.2f}")

    print("\n[SUCCESS] Database seeded successfully!")
    print(f"   Customers: {len(inserted_customers)}")
    print(f"   Transactions: {len(inserted_txns)}")
    print(f"   Failed (processable): {failed_count}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    seed_database()
