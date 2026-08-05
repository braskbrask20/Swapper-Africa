-- Production PostgreSQL baseline. Apply through your migration runner before deploying.
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(320) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'customer',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE swaps (
  id BIGSERIAL PRIMARY KEY,
  reference VARCHAR(32) UNIQUE NOT NULL,
  user_id BIGINT NOT NULL REFERENCES users(id),
  from_asset VARCHAR(12) NOT NULL,
  to_asset VARCHAR(12) NOT NULL,
  amount NUMERIC(24,8) NOT NULL,
  amount_received NUMERIC(24,8) NOT NULL,
  fee NUMERIC(24,8) NOT NULL,
  status VARCHAR(24) NOT NULL DEFAULT 'pending',
  provider_reference VARCHAR(128),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX swaps_user_id_created_at_idx ON swaps(user_id, created_at DESC);
CREATE TABLE audit_logs (
  id BIGSERIAL PRIMARY KEY,
  actor_id BIGINT REFERENCES users(id),
  action VARCHAR(120) NOT NULL,
  entity_type VARCHAR(80) NOT NULL,
  entity_id VARCHAR(80) NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
