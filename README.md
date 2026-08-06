# Swapper Africa

Swapper Africa is a web client and API for a crypto swap product. Signed-in users get real, backend-owned balances and swap history (seeded with demo funds — see `LAUNCH_CHECKLIST.md` for what's still needed before real money moves); signed-out visitors get a local-browser-only demo of the same flow. The `backend/` FastAPI service also serves the frontend directly (see "Deploy to Render" below), so the whole thing is one deployable unit.

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

## Deploy to Render

The backend serves the frontend directly (`backend/app/main.py` mounts the frontend as static files after every API route), so this is a single Render **Web Service** plus a **PostgreSQL** database — one URL, no separate frontend host, no CORS to configure.

**Fastest path — Blueprint** (`render.yaml` at the repo root describes both pieces):

1. Push this repo to GitHub (Render deploys from a connected repo).
2. In Render: **New +** → **Blueprint** → select this repo → Render reads `render.yaml` and shows you the web service + database it's about to create.
3. It'll prompt for `ADMIN_EMAIL` and `ADMIN_PASSWORD` directly (marked `sync: false` in the blueprint, so they're typed straight into Render's dashboard — never shared anywhere else). Use a real email and a strong password; this becomes the bootstrap admin account (`/admin/index.html`).
4. Click **Apply**. Render builds the Docker image, provisions Postgres, wires `DATABASE_URL` automatically, and generates `JWT_SECRET` for you.
5. Once it's live, note the actual assigned URL (Render appends a random suffix if `swapper-africa` is already taken elsewhere, e.g. `swapper-africa-a1b2.onrender.com`). If it differs from the `ALLOWED_ORIGINS` value baked into `render.yaml`, update that env var in the dashboard to match — the service redeploys automatically on env var changes. (This matters less than usual since the frontend and API are same-origin, but it's still correct to keep it accurate.)
6. Visit `/health` on the deployed URL — should return `{"status":"ok","database":"ok",...}`. That's Render's own health check path too (set via `healthCheckPath` in the blueprint), so Render will consider the deploy unhealthy if the database isn't reachable.

If the Blueprint doesn't parse (Render's schema does evolve — worth a quick check against their current Blueprint docs if so), the equivalent manual steps: create a Postgres instance first, then a Web Service pointed at this repo with **Root/Build Context = repo root**, **Dockerfile path = `backend/Dockerfile`**, and set the same env vars (`ENVIRONMENT=production`, `DATABASE_URL` = the Postgres instance's internal connection string, `JWT_SECRET` = a long random value e.g. `openssl rand -hex 32`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ALLOWED_ORIGINS` = the service's URL) plus health check path `/health`.

No manual migration step is needed on first deploy — the app creates its full schema on startup against an empty database. The numbered files in `backend/migrations/` matter later, for evolving an *existing* production database.

**Known limitation, confirm before relying on it**: Render's free Postgres tier has historically been time-limited (expires after a set number of days, then needs a paid plan to keep the data) — check the current terms in Render's dashboard at signup, since pricing/tier details change.

**Before this handles real money**, see `LAUNCH_CHECKLIST.md` in full — this deployment gets the app *live*, it doesn't by itself satisfy custody, KYC/AML, or licensing requirements. The API intentionally does not custody funds or execute blockchain transactions on its own.

## Core endpoints

- `POST /v1/auth/register`, `POST /v1/auth/login`, `GET /v1/auth/me`
- `POST /v1/quotes`, `POST /v1/swaps`, `GET /v1/swaps`
- `GET /v1/admin/summary`, `GET /v1/admin/swaps`, `PATCH /v1/admin/swaps/{reference}`

Admin operations are role-protected. The bootstrap administrator is created from the environment variables at API startup; change the placeholder password before any deployment.
