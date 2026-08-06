import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .models import AccountToken, AuditLog, Balance, Swap, User
from .schemas import (BalanceResponse, CreateSwapRequest, EmailVerificationConfirm, EmailVerificationRequestResponse,
                      LoginRequest, PasswordResetConfirm, PasswordResetRequest, PasswordResetResponse, QuoteRequest,
                      QuoteResponse, RegisterRequest, SwapResponse, TokenResponse, UpdateKycStatusRequest,
                      UpdateSwapStatusRequest, UserResponse)
from .security import (bearer_scheme, create_access_token, decode_access_token, generate_token, hash_password,
                       hash_token, verify_password)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("swapper")

settings = get_settings()
app = FastAPI(title="Swapper Africa API", version="1.0.0", docs_url="/docs" if settings.environment != "production" else None)
cors_options = {"allow_origins": settings.cors_origins, "allow_credentials": True, "allow_methods": ["GET", "POST", "PATCH"], "allow_headers": ["Authorization", "Content-Type"]}
if settings.environment == "development":
    # Dev convenience only: lets the frontend be tested from another device on the same
    # network (e.g. a phone) without hand-editing ALLOWED_ORIGINS for every LAN IP. Never
    # applies when environment=production.
    cors_options["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?$"
app.add_middleware(CORSMiddleware, **cors_options)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Whatever monitoring vendor we eventually pick (see LAUNCH_CHECKLIST.md) plugs in
    # right here -- this is the one place every unhandled failure already passes through.
    logger.exception("unhandled_error path=%s method=%s", request.url.path, request.method)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Something went wrong. Please try again."})


RATES = {"BTC": 118000, "ETH": 3800, "USDT": 1, "SOL": 180}
# There is no licensed custody/liquidity provider wired up yet (see LAUNCH_CHECKLIST.md), so
# every account is seeded with the same demo balances the old browser-local demo used, and swaps
# settle instantly instead of sitting in "pending". Real balances land when that provider does.
DEMO_STARTING_BALANCES = {"BTC": 1, "ETH": 5, "USDT": 10000, "SOL": 20}
RESET_TOKEN_MINUTES = 30
VERIFICATION_TOKEN_MINUTES = 60 * 24

_rate_limit_state: dict[str, list[float]] = {}
_rate_limit_lock = threading.Lock()


def reset_rate_limits() -> None:
    """Test-only: clears in-memory rate-limit counters so tests don't leak state into each other."""
    with _rate_limit_lock:
        _rate_limit_state.clear()


def rate_limit(key_prefix: str, max_attempts: int, window_seconds: int):
    # Single-instance, in-memory sliding window keyed by client IP. A multi-instance
    # production deployment would need a shared store (e.g. Redis) -- a deployment-time
    # concern, not worth building before there's more than one instance to coordinate.
    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{key_prefix}:{client_ip}"
        now = time.monotonic()
        with _rate_limit_lock:
            attempts = [t for t in _rate_limit_state.get(key, []) if now - t < window_seconds]
            if len(attempts) >= max_attempts:
                retry_after = max(1, int(window_seconds - (now - attempts[0])) + 1)
                logger.warning("rate_limited key=%s ip=%s", key_prefix, client_ip)
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Too many attempts. Try again in {retry_after} seconds.", headers={"Retry-After": str(retry_after)})
            attempts.append(now)
            _rate_limit_state[key] = attempts
    return dependency


def sync_sqlite_columns() -> None:
    # Base.metadata.create_all only creates missing tables, it never alters an existing one --
    # fine for Postgres (numbered migrations under backend/migrations/ own that there), but local
    # SQLite dev has no migration runner. Bring an existing dev DB's `users` table up to date
    # in place so accounts created before this phase keep working without a manual step.
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.connect() as conn:
        existing_columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()}
        if existing_columns and "is_email_verified" not in existing_columns:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN NOT NULL DEFAULT 0")
        if existing_columns and "token_version" not in existing_columns:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0")
        if existing_columns and "kyc_status" not in existing_columns:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN kyc_status VARCHAR(20) NOT NULL DEFAULT 'not_started'")
        conn.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    sync_sqlite_columns()
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if not admin:
            db.add(User(email=settings.admin_email.lower(), full_name="Platform Administrator", password_hash=hash_password(settings.admin_password), role="admin"))
            db.commit()


def current_user(credentials=Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(credentials)
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account unavailable")
    if payload.get("ver") != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


def make_quote(request: QuoteRequest) -> QuoteResponse:
    if request.from_asset == request.to_asset:
        raise HTTPException(status_code=422, detail="Assets must be different")
    gross = request.amount * RATES[request.from_asset] / RATES[request.to_asset]
    fee = gross * 0.0025
    return QuoteResponse(rate=RATES[request.from_asset] / RATES[request.to_asset], fee=fee, received=gross - fee, expires_at=datetime.now(timezone.utc) + timedelta(seconds=60))


def swap_response(swap: Swap) -> SwapResponse:
    return SwapResponse(reference=swap.reference, from_asset=swap.from_asset, to_asset=swap.to_asset, amount=float(swap.amount), amount_received=float(swap.amount_received), fee=float(swap.fee), status=swap.status, created_at=swap.created_at)


def ensure_balances(db: Session, user: User) -> dict[str, Balance]:
    rows = {row.asset: row for row in db.scalars(select(Balance).where(Balance.user_id == user.id))}
    created = False
    for asset, amount in DEMO_STARTING_BALANCES.items():
        if asset not in rows:
            row = Balance(user_id=user.id, asset=asset, amount=amount)
            db.add(row)
            rows[asset] = row
            created = True
    if created:
        db.commit()
        for row in rows.values():
            db.refresh(row)
    return rows


def _aware(value: datetime) -> datetime:
    # SQLite drops tzinfo on round-trip even for DateTime(timezone=True) columns; Postgres
    # doesn't. Normalize to UTC-aware either way before doing datetime arithmetic on it.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def issue_account_token(db: Session, user: User, purpose: str, minutes_valid: int) -> str:
    raw_token = generate_token()
    db.add(AccountToken(user_id=user.id, purpose=purpose, token_hash=hash_token(raw_token), expires_at=datetime.now(timezone.utc) + timedelta(minutes=minutes_valid)))
    db.commit()
    return raw_token


def consume_account_token(db: Session, raw_token: str, purpose: str) -> AccountToken:
    token_row = db.scalar(select(AccountToken).where(AccountToken.token_hash == hash_token(raw_token), AccountToken.purpose == purpose))
    if not token_row or token_row.used_at or _aware(token_row.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This link is invalid or has expired.")
    token_row.used_at = datetime.now(timezone.utc)
    db.commit()
    return token_row


@app.get("/health")
def health(response: Response, db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        logger.exception("health_check_database_unreachable")
        database_status = "unreachable"
    if database_status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if database_status == "ok" else "degraded", "environment": settings.environment, "database": database_status}


@app.post("/v1/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit("register", 20, 600))])
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = request.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, full_name=request.full_name, password_hash=hash_password(request.password))
    db.add(user)
    db.flush()
    db.add(AuditLog(actor_id=user.id, action="user.registered", entity_type="user", entity_id=str(user.id)))
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id, user.role, user.token_version))


@app.post("/v1/auth/login", response_model=TokenResponse, dependencies=[Depends(rate_limit("login", 20, 600))])
def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if not user or not verify_password(request.password, user.password_hash) or not user.is_active:
        logger.warning("login_failed email=%s", request.email.lower())
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id, user.role, user.token_version))


@app.get("/v1/auth/me", response_model=UserResponse)
def me(user: User = Depends(current_user)) -> User:
    return user


@app.post("/v1/auth/password-reset/request", response_model=PasswordResetResponse, dependencies=[Depends(rate_limit("password-reset-request", 10, 600))])
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)) -> PasswordResetResponse:
    detail = "If that email has an account, a reset link has been sent."
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if not user:
        return PasswordResetResponse(detail=detail)
    raw_token = issue_account_token(db, user, "password_reset", RESET_TOKEN_MINUTES)
    # send_reset_email(user, raw_token) is the seam for real delivery once a provider is
    # chosen (LAUNCH_CHECKLIST.md). Until then, dev mode surfaces the token directly so the
    # whole flow is testable without a live inbox.
    if settings.environment != "production":
        print(f"[dev] password reset token for {user.email}: {raw_token}")
        return PasswordResetResponse(detail=detail, dev_reset_token=raw_token)
    return PasswordResetResponse(detail=detail)


@app.post("/v1/auth/password-reset/confirm", response_model=TokenResponse)
def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)) -> TokenResponse:
    token_row = consume_account_token(db, request.token, "password_reset")
    user = db.get(User, token_row.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired.")
    user.password_hash = hash_password(request.new_password)
    user.token_version += 1
    db.add(AuditLog(actor_id=user.id, action="user.password_reset", entity_type="user", entity_id=str(user.id)))
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, user.role, user.token_version))


@app.post("/v1/auth/verify-email/request", response_model=EmailVerificationRequestResponse, dependencies=[Depends(rate_limit("verify-email-request", 10, 600))])
def request_email_verification(user: User = Depends(current_user), db: Session = Depends(get_db)) -> EmailVerificationRequestResponse:
    if user.is_email_verified:
        return EmailVerificationRequestResponse(detail="Your email is already verified.")
    raw_token = issue_account_token(db, user, "email_verification", VERIFICATION_TOKEN_MINUTES)
    if settings.environment != "production":
        print(f"[dev] email verification token for {user.email}: {raw_token}")
        return EmailVerificationRequestResponse(detail="Verification email sent.", dev_verification_token=raw_token)
    return EmailVerificationRequestResponse(detail="Verification email sent.")


@app.post("/v1/auth/verify-email/confirm", response_model=UserResponse)
def confirm_email_verification(request: EmailVerificationConfirm, db: Session = Depends(get_db)) -> User:
    token_row = consume_account_token(db, request.token, "email_verification")
    user = db.get(User, token_row.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired.")
    user.is_email_verified = True
    db.commit()
    db.refresh(user)
    return user


@app.post("/v1/auth/sign-out-everywhere", response_model=TokenResponse)
def sign_out_everywhere(user: User = Depends(current_user), db: Session = Depends(get_db)) -> TokenResponse:
    user.token_version += 1
    db.add(AuditLog(actor_id=user.id, action="user.sign_out_everywhere", entity_type="user", entity_id=str(user.id)))
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, user.role, user.token_version))


@app.post("/v1/quotes", response_model=QuoteResponse)
def quote(request: QuoteRequest) -> QuoteResponse:
    return make_quote(request)


@app.get("/v1/balances", response_model=list[BalanceResponse])
def balances(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[BalanceResponse]:
    rows = ensure_balances(db, user)
    return [BalanceResponse(asset=asset, amount=float(row.amount)) for asset, row in rows.items()]


@app.post("/v1/swaps", response_model=SwapResponse, status_code=status.HTTP_201_CREATED)
def create_swap(request: CreateSwapRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> SwapResponse:
    quote = make_quote(request)
    if abs(quote.received - request.expected_received) > max(0.000001, quote.received * 0.005):
        raise HTTPException(status_code=409, detail="Quote changed. Request a new quote before confirming.")
    balances = ensure_balances(db, user)
    from_balance = balances[request.from_asset]
    if float(from_balance.amount) < request.amount:
        raise HTTPException(status_code=409, detail=f"Insufficient {request.from_asset} balance for this swap.")
    to_balance = balances[request.to_asset]
    from_balance.amount = float(from_balance.amount) - request.amount
    to_balance.amount = float(to_balance.amount) + quote.received
    swap = Swap(reference=f"SWP-{uuid4().hex[:10].upper()}", user_id=user.id, from_asset=request.from_asset, to_asset=request.to_asset, amount=request.amount, amount_received=quote.received, fee=quote.fee, status="completed")
    db.add(swap)
    db.flush()
    db.add(AuditLog(actor_id=user.id, action="swap.created", entity_type="swap", entity_id=swap.reference, metadata_json={"status": "completed"}))
    db.commit()
    db.refresh(swap)
    return swap_response(swap)


@app.get("/v1/swaps", response_model=list[SwapResponse])
def list_swaps(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[SwapResponse]:
    swaps = db.scalars(select(Swap).where(Swap.user_id == user.id).order_by(Swap.created_at.desc())).all()
    return [swap_response(swap) for swap in swaps]


@app.get("/v1/admin/summary")
def admin_summary(_: User = Depends(admin_user), db: Session = Depends(get_db)) -> dict:
    return {"users": db.scalar(select(func.count(User.id))), "swaps": db.scalar(select(func.count(Swap.id))), "pending_swaps": db.scalar(select(func.count(Swap.id)).where(Swap.status.in_(["pending", "processing"]))), "completed_volume_usd": float(db.scalar(select(func.coalesce(func.sum(Swap.amount_received), 0)).where(Swap.to_asset == "USDT", Swap.status == "completed")))}


@app.get("/v1/admin/swaps", response_model=list[SwapResponse])
def admin_swaps(_: User = Depends(admin_user), db: Session = Depends(get_db)) -> list[SwapResponse]:
    return [swap_response(swap) for swap in db.scalars(select(Swap).order_by(Swap.created_at.desc()).limit(100)).all()]


@app.patch("/v1/admin/swaps/{reference}", response_model=SwapResponse)
def update_swap(reference: str, request: UpdateSwapStatusRequest, admin: User = Depends(admin_user), db: Session = Depends(get_db)) -> SwapResponse:
    swap = db.scalar(select(Swap).where(Swap.reference == reference))
    if not swap:
        raise HTTPException(status_code=404, detail="Swap not found")
    swap.status, swap.provider_reference = request.status, request.provider_reference
    db.add(AuditLog(actor_id=admin.id, action="swap.status_updated", entity_type="swap", entity_id=reference, metadata_json={"status": request.status}))
    db.commit()
    db.refresh(swap)
    return swap_response(swap)


@app.get("/v1/admin/users", response_model=list[UserResponse])
def admin_users(_: User = Depends(admin_user), db: Session = Depends(get_db)) -> list[User]:
    return db.scalars(select(User).order_by(User.created_at.desc())).all()


@app.patch("/v1/admin/users/{user_id}/kyc", response_model=UserResponse)
def update_kyc_status(user_id: int, request: UpdateKycStatusRequest, admin: User = Depends(admin_user), db: Session = Depends(get_db)) -> User:
    # Manual review only -- there's no ID-verification vendor wired up yet, this is an admin
    # marking an account after looking at it themselves. See LAUNCH_CHECKLIST.md.
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.kyc_status = request.status
    db.add(AuditLog(actor_id=admin.id, action="user.kyc_status_updated", entity_type="user", entity_id=str(user_id), metadata_json={"status": request.status}))
    db.commit()
    db.refresh(user)
    return user


def find_frontend_dir() -> Optional[Path]:
    # Two possible layouts depending on how this process was started: the Docker image
    # (built from repo root, see backend/Dockerfile) copies the frontend alongside `app/`,
    # one level up from this file; running straight from a repo checkout (`--app-dir backend`)
    # has it two levels up, at the repo root. Try both; mount nothing if neither has it (e.g.
    # a stripped-down checkout or build context without the frontend copied) rather than crashing.
    here = Path(__file__).resolve().parent
    for candidate in (here.parent, here.parent.parent):
        if (candidate / "index.html").exists():
            return candidate
    return None


# Mounted last, after every route above, so explicit API routes always take precedence over
# this catch-all -- Starlette matches routes in registration order.
_frontend_dir = find_frontend_dir()
if _frontend_dir:
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
