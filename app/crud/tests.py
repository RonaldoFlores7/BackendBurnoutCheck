from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from fastapi import HTTPException, status
from datetime import datetime, date
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


def get_user_tests(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> List[Test]:
    """Obtiene todos los tests de un usuario con paginación y filtro opcional por fecha."""
    query = db.query(Test).filter(Test.user_id == user_id)

    if date_from:
        query = query.filter(Test.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Test.created_at <= datetime.combine(date_to, datetime.max.time()))

    return query.order_by(Test.created_at.desc()).offset(skip).limit(limit).all()


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


def get_users_tests_report(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> list:
    """
    Retorna todos los usuarios con sus tests completados y resultado de cada uno.
    Filtra por rango de fechas sobre completed_at si se proporcionan.
    Solo incluye tests con status COMPLETED.
    """
    from app.models.user import User

    query = db.query(Test, TestResult, User).outerjoin(
        TestResult, TestResult.test_id == Test.id
    ).join(
        User, User.id == Test.user_id
    ).filter(Test.status == TestStatus.COMPLETED)

    if date_from:
        query = query.filter(Test.completed_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(Test.completed_at <= datetime.combine(date_to, datetime.max.time()))

    rows = query.order_by(User.id, Test.completed_at.desc()).all()

    # Agrupar por usuario
    users_map: dict = {}
    for test, result, user in rows:
        if user.id not in users_map:
            users_map[user.id] = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "tests": []
            }
        users_map[user.id]["tests"].append({
            "test_id": test.id,
            "completed_at": test.completed_at,
            "prediction": result.prediction if result else None,
            "probability": result.probability if result else None,
        })

    return list(users_map.values())


def get_burnout_stats(db: Session) -> dict:
    """
    Retorna estadísticas globales de resultados de burnout.
    Cuenta todos los test_results agrupados por prediction.
    """
    from sqlalchemy import func

    results = db.query(
        TestResult.prediction,
        func.count(TestResult.id).label("count")
    ).group_by(TestResult.prediction).all()

    stats = {row.prediction: row.count for row in results}

    burnout_yes = stats.get(PredictionResult.S, 0)
    burnout_no = stats.get(PredictionResult.N, 0)
    total = burnout_yes + burnout_no

    return {
        "total_completed_tests": total,
        "burnout_yes": burnout_yes,
        "burnout_no": burnout_no,
        "burnout_yes_percentage": round((burnout_yes / total * 100), 2) if total > 0 else 0.0,
        "burnout_no_percentage": round((burnout_no / total * 100), 2) if total > 0 else 0.0,
    }


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
