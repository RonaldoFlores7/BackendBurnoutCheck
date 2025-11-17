from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.enums import PredictionResult


class RecommendationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    for_positive_result: bool = True
    active: bool = True


class RecommendationCreate(RecommendationBase):
    """Schema para crear recomendación"""
    pass


class RecommendationUpdate(BaseModel):
    """Schema para actualizar recomendación"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    for_positive_result: Optional[bool] = None
    active: Optional[bool] = None


class RecommendationResponse(RecommendationBase):
    """Schema de respuesta de recomendación"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestResultBase(BaseModel):
    prediction: PredictionResult
    probability: float = Field(..., ge=0.0, le=1.0)
    model_version: str = Field(..., min_length=1, max_length=50)


class TestResultCreate(TestResultBase):
    """Schema para crear resultado (usado internamente)"""
    test_id: int


class TestResultResponse(TestResultBase):
    """Schema de respuesta básica de resultado"""
    id: int
    test_id: int
    predicted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestResultDetailResponse(TestResultResponse):
    """Schema detallado con recomendaciones incluidas"""
    recommendations: List[RecommendationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class QuestionResponses(BaseModel):
    """Schema para enviar al servicio ML externo"""
    ciclo: int
    genero: str
    facultad: str
    practicasprepro: str
    pregunta1: str
    pregunta2: str
    pregunta3: str
    pregunta4: str
    pregunta5: str
    pregunta6: str
    pregunta7: str
    pregunta8: str
    pregunta9: str
    pregunta10: str
    pregunta11: str
    pregunta12: str
    pregunta13: str
    pregunta14: str
    pregunta15: str
    pregunta16: str
    pregunta17: str
    pregunta18: str
    pregunta19: str


class MLPredictionRequest(BaseModel):
    respuestas: QuestionResponses


class MLPredictionResponse(BaseModel):
    """Schema de respuesta del servicio ML externo"""
    resultado: str  # "S" o "N"
    probabilidad: float
    model_version: str