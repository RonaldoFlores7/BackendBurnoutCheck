from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    """Schema para registro de nuevo usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class LoginRequest(BaseModel):
    """Schema para login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)


class TokenRefresh(BaseModel):
    """Schema para refresh token (si lo implementas)"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema de respuesta de autenticación"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # Minutos hasta expiración


class TokenData(BaseModel):
    """Schema para datos dentro del token JWT"""
    sub: str  # username o user_id
    role: Optional[str] = None