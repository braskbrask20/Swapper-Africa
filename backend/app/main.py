from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .models import AuditLog, Swap, User
from .schemas import (CreateSwapRequest, LoginRequest, QuoteRequest, QuoteResponse,
                      RegisterRequest, SwapResponse, TokenResponse, UpdateSwapStatusRequest, UserResponse)
from .security import bearer_scheme, create_access_token, decode_access_token, hash_password, verify_password

settings = get_settings()
app = FastAPI(title="Swapper Africa API", version="1.0.0", docs_url="/docs" if settings.environment != "production" else None)
cors_options = {"allow_origins": settings.cors_origins, "allow_credentials": True, "allow_methods": ["GET", "POST", "PATCH"], "allow_headers": ["Authorization", "Content-Type"]}
if settings.environment == "development":
    # Dev convenience only: lets the frontend be tested from another device on the same
    # network (e.g. a phone) without hand-editing ALLOWED_ORIGINS for every LAN IP. Never
    # applies when environment=production.
    cors_options["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?$"
app.add_middleware(CORSMiddleware, **cors_options)
RATES = {"BTC": 118000, "ETH": 3800, "USDT": 1, "SOL": 180}


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


@app.post("/v1/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = request.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, full_name=request.full_name, password_hash=hash_password(request.password))
    db.add(user)
    db.flush()
    db.add(AuditLog(actor_id=user.id, action="user.registered", entity_type="user", entity_id=str(user.id)))
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@app.post("/v1/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if not user or not verify_password(request.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@app.get("/v1/auth/me", response_model=UserResponse)
def me(user: User = Depends(current_user)) -> User:
    return user


@app.post("/v1/quotes", response_model=QuoteResponse)
def quote(request: QuoteRequest) -> QuoteResponse:
    return make_quote(request)


@app.post("/v1/swaps", response_model=SwapResponse, status_code=status.HTTP_201_CREATED)
def create_swap(request: CreateSwapRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> SwapResponse:
    quote = make_quote(request)
    if abs(quote.received - request.expected_received) > max(0.000001, quote.received * 0.005):
        raise HTTPException(status_code=409, detail="Quote changed. Request a new quote before confirming.")
    swap = Swap(reference=f"SWP-{uuid4().hex[:10].upper()}", user_id=user.id, from_asset=request.from_asset, to_asset=request.to_asset, amount=request.amount, amount_received=quote.received, fee=quote.fee, status="pending")
    db.add(swap)
    db.flush()
    db.add(AuditLog(actor_id=user.id, action="swap.created", entity_type="swap", entity_id=swap.reference))
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
