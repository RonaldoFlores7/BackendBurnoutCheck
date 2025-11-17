from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class QuestionOptionBase(BaseModel):
    option_text: str = Field(..., min_length=1, max_length=100)
    option_value: str = Field(..., min_length=1, max_length=100)
    order: int = Field(..., ge=1)


class QuestionOptionCreate(QuestionOptionBase):
    pass


class QuestionOptionResponse(QuestionOptionBase):
    id: int
    question_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    question_key: str = Field(..., min_length=1, max_length=50)
    question_text: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    order: int = Field(..., ge=1)
    active: bool = True


class QuestionCreate(QuestionBase):
    """Schema para crear pregunta con opciones"""
    options: List[QuestionOptionCreate] = Field(..., min_items=2)


class QuestionUpdate(BaseModel):
    """Schema para actualizar pregunta (campos opcionales)"""
    question_text: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    order: Optional[int] = Field(None, ge=1)
    active: Optional[bool] = None


class QuestionResponse(QuestionBase):
    """Schema de respuesta con opciones incluidas"""
    id: int
    options: List[QuestionOptionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionListResponse(BaseModel):
    """Schema simplificado para listado"""
    id: int
    question_key: str
    question_text: str
    order: int
    active: bool

    model_config = ConfigDict(from_attributes=True)