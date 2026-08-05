# Launch checklist

## Technical controls

- [ ] Set production `DATABASE_URL`, `JWT_SECRET`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` in a managed secret store.
- [ ] Use managed PostgreSQL, apply the initial migration, enable backups, and test restoration.
- [ ] Set `ENVIRONMENT=production` and a strict list of HTTPS `ALLOWED_ORIGINS`.
- [ ] Put the API behind HTTPS, a WAF, request-size limits, rate limiting, and centralized error monitoring.
- [ ] Replace fixed demo rates with an authenticated market-data/liquidity provider.
- [ ] Integrate a licensed custody/liquidity provider and verify webhooks with signed payloads and idempotency keys.
- [ ] Add email verification, password resets, MFA for admins, and user session revocation.
- [ ] Complete independent security testing and dependency scanning.

## Operations and legal

- [ ] Define swap approval, exception, incident response, and reconciliation procedures.
- [ ] Enable KYC/AML, sanctions screening, transaction monitoring, and required reporting.
- [ ] Obtain legal and licensing review in every country where the service is available.
- [ ] Publish a privacy policy, terms, risk disclosures, support contact, and data-retention policy.
- [ ] Prepare App Store / Play Store privacy disclosures, test accounts, screenshots, and support URL.

## Product release

- [ ] Replace browser-local demo balances with authenticated API calls in the public client.
- [ ] Run end-to-end tests against a staging provider account.
- [ ] Conduct a closed beta and accessibility review.
- [ ] Obtain product, operations, security, and legal sign-off.
