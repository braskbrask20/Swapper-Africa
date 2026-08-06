# Launch checklist

## Technical controls

- [ ] Set production `DATABASE_URL`, `JWT_SECRET`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` in a managed secret store.
- [ ] Use managed PostgreSQL, apply `backend/migrations/001_initial.sql` through `003_security_hardening.sql` in order, enable backups, and test restoration.
  - **Backup procedure** (concrete, once a real Postgres instance exists): if using a managed provider (RDS, Supabase, Neon, Railway, etc.), enable its automatic daily backups + point-in-time recovery first — that's the simpler default and covers most cases on its own.
  - Manual/scripted backup: `pg_dump --format=custom --file=swapper-$(date +%Y%m%d%H%M).dump "$DATABASE_URL"`, stored somewhere other than the DB host (S3/GCS bucket, etc.), on a daily cron.
  - Restore: `pg_restore --clean --if-exists --dbname="$DATABASE_URL" swapper-<timestamp>.dump`.
  - **Test restoration before launch**: restore a backup into a throwaway database and confirm the app boots against it — an untested backup is not a backup.
- [ ] Set `ENVIRONMENT=production` and a strict list of HTTPS `ALLOWED_ORIGINS`.
- [x] Basic rate limiting on auth endpoints (in-memory, single-instance — upgrade to a shared store like Redis once there's more than one backend instance).
- [ ] Put the API behind HTTPS, a WAF, and request-size limits.
- [x] Structured logging + a global error handler exist (`backend/app/main.py`); still need a real monitoring vendor (Sentry, etc.) wired into that same seam.
- [ ] Replace fixed demo rates with an authenticated market-data/liquidity provider.
- [ ] Integrate a licensed custody/liquidity provider and verify webhooks with signed payloads and idempotency keys.
- [x] Email verification, password resets, and user session revocation (`POST /v1/auth/sign-out-everywhere`) are implemented — password reset/verification emails still need a real provider wired into the `send_reset_email`/dev-mode seam in `main.py`.
- [ ] Add MFA for admin accounts.
- [ ] Complete independent security testing and dependency scanning.

## Operations and legal

- [ ] Define swap approval, exception, incident response, and reconciliation procedures.
- [ ] Enable KYC/AML, sanctions screening, transaction monitoring, and required reporting.
- [ ] Obtain legal and licensing review in every country where the service is available.
- [ ] Publish a privacy policy, terms, risk disclosures, support contact, and data-retention policy.
- [ ] Prepare App Store / Play Store privacy disclosures, test accounts, screenshots, and support URL.

## Product release

- [x] Replace browser-local demo balances with authenticated API calls in the public client (guest/signed-out visitors still get the local demo).
- [ ] Run end-to-end tests against a staging provider account.
- [ ] Conduct a closed beta and accessibility review.
- [ ] Obtain product, operations, security, and legal sign-off.
