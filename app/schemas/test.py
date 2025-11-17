from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import TestStatus


class TestBase(BaseModel):
    ciclo: int = Field(..., ge=1, le=20)
    genero: str = Field(..., min_length=1, max_length=50)
    facultad: str = Field(..., min_length=1, max_length=255)
    practicasprepro: str = Field(..., pattern="^(Sí|No)$")  # Solo "Sí" o "No"


class TestCreate(TestBase):
    """Schema para iniciar un test (solo datos demográficos)"""
    pass


class TestResponseSubmit(BaseModel):
    """Schema para enviar una respuesta"""
    question_id: int = Field(..., ge=1)
    answer_value: str = Field(..., min_length=1, max_length=100)


class TestResponsesBatch(BaseModel):
    """Schema para enviar múltiples respuestas a la vez"""
    responses: List[TestResponseSubmit] = Field(..., min_items=1)


class TestResponseDetail(BaseModel):
    """Detalle de una respuesta individual"""
    id: int
    question_id: int
    question_key: str
    question_text: str
    answer_value: str
    answered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestResponse(TestBase):
    """Schema de respuesta de test"""
    id: int
    user_id: int
    status: TestStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Contadores útiles
    total_responses: int = 0
    expected_responses: int = 19

    model_config = ConfigDict(from_attributes=True)


class TestDetailResponse(TestResponse):
    """Schema detallado con respuestas incluidas"""
    responses: List[TestResponseDetail] = []

    model_config = ConfigDict(from_attributes=True)


class TestListResponse(BaseModel):
    """Schema simplificado para listado de tests"""
    id: int
    status: TestStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    has_result: bool = False

    model_config = ConfigDict(from_attributes=True)