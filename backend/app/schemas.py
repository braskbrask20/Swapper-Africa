from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class QuoteRequest(BaseModel):
    from_asset: str = Field(pattern="^(BTC|ETH|USDT|SOL)$")
    to_asset: str = Field(pattern="^(BTC|ETH|USDT|SOL)$")
    amount: float = Field(gt=0)


class QuoteResponse(BaseModel):
    rate: float
    fee: float
    received: float
    expires_at: datetime


class CreateSwapRequest(QuoteRequest):
    expected_received: float = Field(gt=0)


class SwapResponse(BaseModel):
    reference: str
    from_asset: str
    to_asset: str
    amount: float
    amount_received: float
    fee: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateSwapStatusRequest(BaseModel):
    status: str = Field(pattern="^(pending|processing|completed|failed|cancelled)$")
    provider_reference: Optional[str] = Field(default=None, max_length=128)
