-- REVA: AI Revenue Recovery Agent
-- Supabase PostgreSQL Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Customers
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  previous_success_rate NUMERIC(5,2) DEFAULT 0.0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_email ON customers(email);

-- 2. Transactions
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  razorpay_payment_id TEXT,
  razorpay_order_id TEXT,
  amount NUMERIC(12,2) NOT NULL,
  currency TEXT DEFAULT 'INR',
  payment_method TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  failure_reason TEXT,
  retry_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_customer ON transactions(customer_id);
CREATE INDEX idx_transactions_status ON transactions(status);

-- 3. Recovery Cases
CREATE TABLE recovery_cases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
  customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  amount_at_risk NUMERIC(12,2) NOT NULL,
  diagnosis TEXT,
  ai_recommendation TEXT,
  selected_action TEXT,
  status TEXT NOT NULL DEFAULT 'OPEN',
  recovered_amount NUMERIC(12,2) DEFAULT 0.0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recovery_cases_status ON recovery_cases(status);
CREATE INDEX idx_recovery_cases_transaction ON recovery_cases(transaction_id);

-- 4. Recovery Actions
CREATE TABLE recovery_actions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  recovery_case_id UUID NOT NULL REFERENCES recovery_cases(id) ON DELETE CASCADE,
  action_type TEXT NOT NULL,
  execution_status TEXT NOT NULL DEFAULT 'PENDING',
  razorpay_payment_link_id TEXT,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recovery_actions_case ON recovery_actions(recovery_case_id);

-- 5. Audit Logs
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  recovery_case_id UUID REFERENCES recovery_cases(id) ON DELETE CASCADE,
  component TEXT NOT NULL,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_case ON audit_logs(recovery_case_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
