-- Manual admin-set KYC status. No ID-verification vendor integrated yet -- see
-- LAUNCH_CHECKLIST.md. Apply through your migration runner before deploying.
ALTER TABLE users ADD COLUMN kyc_status VARCHAR(20) NOT NULL DEFAULT 'not_started';
