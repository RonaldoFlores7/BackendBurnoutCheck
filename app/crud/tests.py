from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from fastapi import HTTPException, status
from datetime import datetime
import pytz

from app.models.test import Test
from app.models.test_response import TestResponse
from app.models.test_result import TestResult
from app.models.question import Question
from app.models.recommendation import Recommendation, TestRecommendation
from app.models.enums import TestStatus, PredictionResult
from app.schemas.test import TestCreate, TestResponseSubmit
from app.schemas.test_result import TestResultCreate


def get_test_by_id(db: Session, test_id: int) -> Optional[Test]:
    """Obtiene un test por ID"""
    return db.query(Test).filter(Test.id == test_id).first()


def get_user_tests(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Test]:
    """Obtiene todos los tests de un usuario con paginación"""
    return db.query(Test).filter(Test.user_id == user_id).order_by(Test.created_at.desc()).offset(skip).limit(limit).all()


def create_test(db: Session, user_id: int, test_data: TestCreate) -> Test:
    """
    Crea un nuevo test para un usuario.
    El test se crea con status IN_PROGRESS.
    """
    new_test = Test(
        user_id=user_id,
        ciclo=test_data.ciclo,
        genero=test_data.genero,
        facultad=test_data.facultad,
        practicasprepro=test_data.practicasprepro,
        status=TestStatus.IN_PROGRESS
    )
    
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    
    return new_test


def add_test_response(db: Session, test_id: int, response_data: TestResponseSubmit) -> TestResponse:
    """
    Agrega una respuesta a un test.
    Valida que:
    - El test exista y esté IN_PROGRESS
    - La pregunta exista
    - No haya duplicados (una pregunta solo se responde una vez)
    """
    # Verificar test
    test = get_test_by_id(db, test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.status != TestStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El test ya está completado"
        )
    
    # Verificar que la pregunta existe
    question = db.query(Question).filter(Question.id == response_data.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )
    
    # Verificar que no haya respuesta duplicada
    existing_response = db.query(TestResponse).filter(
        TestResponse.test_id == test_id,
        TestResponse.question_id == response_data.question_id
    ).first()
    
    if existing_response:
        # Actualizar respuesta existente
        existing_response.answer_value = response_data.answer_value
        db.commit()
        db.refresh(existing_response)
        return existing_response
    
    # Crear nueva respuesta
    new_response = TestResponse(
        test_id=test_id,
        question_id=response_data.question_id,
        answer_value=response_data.answer_value
    )
    
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    
    return new_response


def get_test_responses(db: Session, test_id: int) -> List[TestResponse]:
    """Obtiene todas las respuestas de un test"""
    return db.query(TestResponse).filter(TestResponse.test_id == test_id).all()


def get_test_responses_as_dict(db: Session, test_id: int) -> Dict[str, str]:
    """
    Obtiene las respuestas de un test como diccionario.
    Formato: {question_key: answer_value}
    Útil para enviar al servicio ML.
    """
    responses = db.query(TestResponse, Question).join(
        Question, TestResponse.question_id == Question.id
    ).filter(TestResponse.test_id == test_id).all()
    
    return {question.question_key: response.answer_value for response, question in responses}


def complete_test(db: Session, test_id: int, expected_responses: int = 19) -> Test:
    """
    Marca un test como completado.
    Valida que tenga el número esperado de respuestas.
    """
    test = get_test_by_id(db, test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.status == TestStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El test ya está completado"
        )
    
    # Contar respuestas
    response_count = db.query(TestResponse).filter(TestResponse.test_id == test_id).count()
    
    if response_count < expected_responses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El test requiere {expected_responses} respuestas, solo hay {response_count}"
        )
    
    # Marcar como completado
    test.status = TestStatus.COMPLETED
    test.completed_at = datetime.now(pytz.timezone("America/Lima"))
    
    db.commit()
    db.refresh(test)
    
    return test


def create_test_result(db: Session, result_data: TestResultCreate) -> TestResult:
    """
    Guarda el resultado de la predicción ML.
    """
    # Verificar que el test existe
    test = get_test_by_id(db, result_data.test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    # Verificar que no tenga resultado ya
    existing_result = db.query(TestResult).filter(TestResult.test_id == result_data.test_id).first()
    if existing_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este test ya tiene un resultado"
        )
    
    # Crear resultado
    new_result = TestResult(
        test_id=result_data.test_id,
        prediction=result_data.prediction,
        probability=result_data.probability,
        model_version=result_data.model_version
    )
    
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    
    return new_result


def assign_recommendations(db: Session, test_result_id: int, prediction: PredictionResult) -> List[Recommendation]:
    """
    Asigna recomendaciones a un resultado según la predicción.
    
    - Si prediction = "S": Asigna recomendaciones para resultado positivo
    - Si prediction = "N": Asigna recomendaciones para resultado negativo (o ninguna)
    """
    # Obtener recomendaciones activas según el tipo de predicción
    is_positive = (prediction == PredictionResult.S)
    
    recommendations = db.query(Recommendation).filter(
        Recommendation.active == True,
        Recommendation.for_positive_result == is_positive
    ).all()
    
    # Asignar recomendaciones
    for rec in recommendations:
        test_rec = TestRecommendation(
            test_result_id=test_result_id,
            recommendation_id=rec.id
        )
        db.add(test_rec)
    
    db.commit()
    
    return recommendations


def get_test_result(db: Session, test_id: int) -> Optional[TestResult]:
    """Obtiene el resultado de un test"""
    return db.query(TestResult).filter(TestResult.test_id == test_id).first()


def delete_test(db: Session, test_id: int) -> bool:
    """
    Elimina un test y todas sus respuestas/resultados (cascade).
    Retorna True si se eliminó, False si no existía.
    """
    test = get_test_by_id(db, test_id)
    
    if not test:
        return False
    
    db.delete(test)
    db.commit()
    
    return True