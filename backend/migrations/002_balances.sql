-- Per-user, per-asset balances. Apply through your migration runner before deploying.
CREATE TABLE balances (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  asset VARCHAR(12) NOT NULL,
  amount NUMERIC(24,8) NOT NULL DEFAULT 0,
  CONSTRAINT uq_balance_user_asset UNIQUE (user_id, asset)
);
CREATE INDEX balances_user_id_idx ON balances(user_id);
