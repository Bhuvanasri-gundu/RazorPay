"""Generate realistic synthetic demo data and export to data/synthetic_data.json."""

import json
import os
import random
from datetime import datetime, timedelta

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

PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING"]
FAILURE_REASONS = ["BANK_TIMEOUT", "UPI_TIMEOUT", "CARD_DECLINED", "INSUFFICIENT_BALANCE", "TECHNICAL_FAILURE"]

AMOUNTS = [
    199, 299, 499, 799, 999, 1499, 1999, 2499, 2999, 3999, 4999,
    6999, 8999, 9999, 12999, 14999, 19999, 24999, 29999, 34999,
    44999, 54999, 64999, 74999, 99999
]


def generate_synthetic_dataset(num_customers: int = 120, num_transactions: int = 400):
    customers = []
    used_emails = set()

    for i in range(num_customers):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        base_email = f"{first.lower()}.{last.lower()}"
        domain = "gmail.com" if random.random() > 0.3 else "outlook.com"
        email = f"{base_email}@{domain}"
        idx = 1
        while email in used_emails:
            email = f"{base_email}{idx}@{domain}"
            idx += 1
        used_emails.add(email)

        phone = f"+91{random.randint(7000000000, 9999999999)}"
        success_rate = round(random.uniform(0.20, 0.98), 2)

        customers.append({
            "temp_id": f"cust_{i+1}",
            "name": name,
            "email": email,
            "phone": phone,
            "previous_success_rate": success_rate,
        })

    transactions = []
    now = datetime.utcnow()

    for i in range(num_transactions):
        cust = random.choice(customers)
        amount = random.choice(AMOUNTS)
        method = random.choice(PAYMENT_METHODS)
        created = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

        # ~40% failure rate
        if random.random() < 0.40:
            status = "FAILED"
            if method == "UPI" and random.random() > 0.4:
                failure_reason = "UPI_TIMEOUT"
            elif method == "CARD" and random.random() > 0.4:
                failure_reason = "CARD_DECLINED"
            else:
                failure_reason = random.choice(FAILURE_REASONS)
            retry_count = random.choices([0, 1, 2, 3, 4], weights=[40, 30, 15, 10, 5])[0]
        else:
            status = "SUCCESS"
            failure_reason = None
            retry_count = 0

        transactions.append({
            "temp_customer_id": cust["temp_id"],
            "amount": amount,
            "currency": "INR",
            "payment_method": method,
            "status": status,
            "failure_reason": failure_reason,
            "retry_count": retry_count,
            "created_at": created.isoformat(),
        })

    return {"customers": customers, "transactions": transactions}


def main():
    data = generate_synthetic_dataset(120, 400)
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "data"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_data.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    failed_count = sum(1 for t in data["transactions"] if t["status"] == "FAILED")
    total_risk = sum(t["amount"] for t in data["transactions"] if t["status"] == "FAILED")
    print(f"Generated {len(data['customers'])} customers and {len(data['transactions'])} transactions.")
    print(f"Failed transactions (revenue at risk): {failed_count} (INR {total_risk:,.2f})")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
