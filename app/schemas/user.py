from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import UserRole


# ==================== BASE SCHEMAS ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    name: str = Field(default="", max_length=100)
    lastname: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=50)
    role: UserRole = UserRole.USER


# ==================== REQUEST SCHEMAS ====================

class UserCreate(UserBase):
    """Schema para crear usuario (incluye password)"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema para actualizar usuario (todos los campos opcionales)"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=100)
    lastname: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    role: Optional[UserRole] = None
    active: Optional[bool] = None


class UserChangePassword(BaseModel):
    """Schema para cambiar contraseña"""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, max_length=100)


# ==================== RESPONSE SCHEMAS ====================

class UserResponse(UserBase):
    """Schema de respuesta básica (sin password)"""
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    """Schema detallado con estadísticas (opcional)"""
    total_tests: int = 0
    completed_tests: int = 0

    model_config = ConfigDict(from_attributes=True)