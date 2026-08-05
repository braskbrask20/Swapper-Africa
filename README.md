# Swapper Africa

Swapper Africa is a web client and API foundation for a crypto swap product. The current public pages remain a local-data demo; the `backend/` service is the secure server foundation for authenticated users, provider-backed swap execution, and administrative operations.

## Local setup

1. Create a backend environment: `cp backend/.env.example backend/.env`
2. Replace `JWT_SECRET`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` in `backend/.env`.
3. Install API dependencies: `python3 -m pip install -r backend/requirements.txt`
4. Run locally: `python3 -m uvicorn app.main:app --app-dir backend --reload`
5. Open API docs at `http://localhost:8000/docs` and the operations console at `admin/index.html` (serve the repository via a local web server).

## Production path

Before launch, move to managed PostgreSQL and apply `backend/migrations/001_initial.sql`. Deploy the API using the included Dockerfile, configure a strong secret and explicit CORS origins, and use HTTPS only.

The API intentionally does not custody funds or execute blockchain transactions on its own. A production release still requires an approved licensed liquidity/custody provider, KYC/AML and sanctions screening, transaction monitoring, jurisdiction-specific legal review, rate limiting, error monitoring, backups, a privacy policy, terms of service, and mobile-store compliance materials.

## Core endpoints

- `POST /v1/auth/register`, `POST /v1/auth/login`, `GET /v1/auth/me`
- `POST /v1/quotes`, `POST /v1/swaps`, `GET /v1/swaps`
- `GET /v1/admin/summary`, `GET /v1/admin/swaps`, `PATCH /v1/admin/swaps/{reference}`

Admin operations are role-protected. The bootstrap administrator is created from the environment variables at API startup; change the placeholder password before any deployment.
