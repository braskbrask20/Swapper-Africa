# Swapper Africa

Swapper Africa is a web client and API foundation for a crypto swap product. The current public pages remain a local-data demo; the `backend/` service is the secure server foundation for authenticated users, provider-backed swap execution, and administrative operations.

## Local setup

1. Create a backend environment: `cp backend/.env.example backend/.env`
2. Replace `JWT_SECRET`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` in `backend/.env`.
3. Install API dependencies: `python3 -m pip install -r backend/requirements.txt`
4. Run the API: `python3 -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000`
   - `--host 0.0.0.0` is required to test from any browser other than the one on this exact machine (another device on your network, or a browser outside your editor) — `127.0.0.1` (uvicorn's default) only accepts connections from the same machine.
5. Serve the frontend from the repo root: `python3 scripts/dev_frontend_server.py 5500`
   - This is the same as `python3 -m http.server 5500` but also tells the browser never to cache the files — while we're actively changing the JS/CSS, a plain static server lets browsers (Safari especially) hold onto stale copies of individual files, which shows up as confusing "Can't find variable" style errors after an update.
6. Open `http://localhost:8000/docs` for the API docs, `http://localhost:5500` for the site, and `http://localhost:5500/admin/index.html` for the operations console.
7. To test from another device on the same Wi-Fi (e.g. a phone), find this computer's LAN IP (`ipconfig getifaddr en0` on macOS) and open `http://<that-ip>:5500` on the other device — the frontend auto-detects the matching API host, no config needed.

## Production path

Before launch, move to managed PostgreSQL and apply `backend/migrations/001_initial.sql`. Deploy the API using the included Dockerfile, configure a strong secret and explicit CORS origins, and use HTTPS only.

The API intentionally does not custody funds or execute blockchain transactions on its own. A production release still requires an approved licensed liquidity/custody provider, KYC/AML and sanctions screening, transaction monitoring, jurisdiction-specific legal review, rate limiting, error monitoring, backups, a privacy policy, terms of service, and mobile-store compliance materials.

## Core endpoints

- `POST /v1/auth/register`, `POST /v1/auth/login`, `GET /v1/auth/me`
- `POST /v1/quotes`, `POST /v1/swaps`, `GET /v1/swaps`
- `GET /v1/admin/summary`, `GET /v1/admin/swaps`, `PATCH /v1/admin/swaps/{reference}`

Admin operations are role-protected. The bootstrap administrator is created from the environment variables at API startup; change the placeholder password before any deployment.
