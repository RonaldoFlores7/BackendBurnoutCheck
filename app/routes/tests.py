from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.models.enums import PredictionResult
from app.schemas.test import (
    TestCreate,
    TestResponse as TestResponseSchema,
    TestDetailResponse,
    TestListResponse,
    TestResponseSubmit,
    TestResponsesBatch
)
from app.schemas.test_result import TestResultDetailResponse, TestResultCreate
from app.dependencies import get_current_active_user
from app.crud import tests as crud_tests
from app.services.ml_service import ml_service


router = APIRouter()


@router.post("/start", response_model=TestResponseSchema, status_code=status.HTTP_201_CREATED)
def start_test(
    test_data: TestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Inicia un nuevo test para el usuario autenticado.
    
    Crea un test con status IN_PROGRESS y datos demográficos.
    El usuario luego deberá enviar las respuestas.
    """
    test = crud_tests.create_test(db, current_user.id, test_data)
    
    # Preparar respuesta con contadores
    response = TestResponseSchema.model_validate(test)
    response.total_responses = 0
    response.expected_responses = 19
    
    return response


@router.post("/{test_id}/responses", status_code=status.HTTP_201_CREATED)
def submit_response(
    test_id: int,
    response_data: TestResponseSubmit,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Envía una respuesta individual a un test.
    
    Si la pregunta ya fue respondida, actualiza la respuesta.
    """
    # Verificar que el test pertenece al usuario
    test = crud_tests.get_test_by_id(db, test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este test"
        )
    
    # Agregar respuesta
    response = crud_tests.add_test_response(db, test_id, response_data)
    
    # Contar respuestas actuales
    total_responses = db.query(crud_tests.TestResponse).filter(
        crud_tests.TestResponse.test_id == test_id
    ).count()
    
    return {
        "message": "Respuesta guardada",
        "response_id": response.id,
        "total_responses": total_responses,
        "remaining": 19 - total_responses
    }


@router.post("/{test_id}/responses/batch", status_code=status.HTTP_201_CREATED)
def submit_responses_batch(
    test_id: int,
    batch_data: TestResponsesBatch,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Envía múltiples respuestas de una vez.
    
    Útil si el frontend envía todas las respuestas al final.
    """
    # Verificar test
    test = crud_tests.get_test_by_id(db, test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este test"
        )
    
    # Agregar todas las respuestas
    for response_data in batch_data.responses:
        crud_tests.add_test_response(db, test_id, response_data)
    
    total_responses = db.query(crud_tests.TestResponse).filter(
        crud_tests.TestResponse.test_id == test_id
    ).count()
    
    return {
        "message": "Respuestas guardadas",
        "total_responses": total_responses,
        "remaining": 19 - total_responses
    }


@router.post("/{test_id}/complete", response_model=TestResultDetailResponse)
async def complete_test(
    test_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Completa un test y obtiene la predicción del modelo ML.
    
    Flujo:
    1. Valida que el test tenga todas las respuestas (19)
    2. Marca el test como COMPLETED
    3. Envía datos al servicio ML
    4. Guarda el resultado de la predicción
    5. Asigna recomendaciones según la predicción
    6. Retorna el resultado con recomendaciones
    """
    # Verificar test
    test = crud_tests.get_test_by_id(db, test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para completar este test"
        )
    
    # Completar test (valida que tenga 19 respuestas)
    test = crud_tests.complete_test(db, test_id, expected_responses=19)
    
    # Preparar datos para ML
    test_data = {
        "ciclo": test.ciclo,
        "genero": test.genero,
        "facultad": test.facultad,
        "practicasprepro": test.practicasprepro
    }
    
    responses_dict = crud_tests.get_test_responses_as_dict(db, test_id)
    
    # Construir request para ML
    ml_request = ml_service.build_prediction_request(test_data, responses_dict)
    
    # Llamar al servicio ML
    ml_response = await ml_service.predict(ml_request)
    
    # Guardar resultado
    result_data = TestResultCreate(
        test_id=test_id,
        prediction=PredictionResult.S if ml_response.resultado == "SI" else PredictionResult.N,
        probability=ml_response.probabilidad,
        model_version=ml_response.model_version
    )
    
    result = crud_tests.create_test_result(db, result_data)
    
    # Asignar recomendaciones
    recommendations = crud_tests.assign_recommendations(db, result.id, result.prediction)
    
    # Preparar respuesta manualmente para evitar problemas de serialización
    from app.schemas.test_result import RecommendationResponse
    
    result_response = TestResultDetailResponse(
        id=result.id,
        test_id=result.test_id,
        prediction=result.prediction,
        probability=result.probability,
        model_version=result.model_version,
        predicted_at=result.predicted_at,
        recommendations=[RecommendationResponse.model_validate(rec) for rec in recommendations]
    )
    
    return result_response


@router.get("/me", response_model=List[TestListResponse])
def get_my_tests(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de tests del usuario autenticado.
    
    Retorna lista ordenada por fecha (más recientes primero).
    """
    tests = crud_tests.get_user_tests(db, current_user.id, skip, limit)
    
    # Preparar respuesta con indicador de resultado
    result = []
    for test in tests:
        test_data = TestListResponse.model_validate(test)
        test_data.has_result = crud_tests.get_test_result(db, test.id) is not None
        result.append(test_data)
    
    return result


@router.get("/{test_id}", response_model=TestDetailResponse)
def get_test_detail(
    test_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el detalle completo de un test con todas sus respuestas.
    """
    test = crud_tests.get_test_by_id(db, test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este test"
        )
    
    # Obtener respuestas con detalle de preguntas
    from app.models.question import Question
    from app.schemas.test import TestResponseDetail
    
    responses = db.query(crud_tests.TestResponse, Question).join(
        Question, crud_tests.TestResponse.question_id == Question.id
    ).filter(crud_tests.TestResponse.test_id == test_id).all()
    
    # Preparar respuesta manualmente
    response_details = [
        TestResponseDetail(
            id=resp.id,
            question_id=resp.question_id,
            question_key=q.question_key,
            question_text=q.question_text,
            answer_value=resp.answer_value,
            answered_at=resp.answered_at
        )
        for resp, q in responses
    ]
    
    test_data = TestDetailResponse(
        id=test.id,
        user_id=test.user_id,
        ciclo=test.ciclo,
        genero=test.genero,
        facultad=test.facultad,
        practicasprepro=test.practicasprepro,
        status=test.status,
        created_at=test.created_at,
        completed_at=test.completed_at,
        total_responses=len(responses),
        expected_responses=19,
        responses=response_details
    )
    
    return test_data


@router.get("/{test_id}/result", response_model=TestResultDetailResponse)
def get_test_result(
    test_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el resultado y recomendaciones de un test completado.
    """
    test = crud_tests.get_test_by_id(db, test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este resultado"
        )
    
    result = crud_tests.get_test_result(db, test_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este test aún no tiene resultado"
        )
    
    # Obtener recomendaciones reales (no la tabla intermedia)
    from app.models.recommendation import Recommendation, TestRecommendation
    from app.schemas.test_result import RecommendationResponse
    
    recommendations = db.query(Recommendation).join(
        TestRecommendation, TestRecommendation.recommendation_id == Recommendation.id
    ).filter(TestRecommendation.test_result_id == result.id).all()
    
    # Construir respuesta manualmente
    result_response = TestResultDetailResponse(
        id=result.id,
        test_id=result.test_id,
        prediction=result.prediction,
        probability=result.probability,
        model_version=result.model_version,
        predicted_at=result.predicted_at,
        recommendations=[RecommendationResponse.model_validate(rec) for rec in recommendations]
    )
    
    return result_response


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test(
    test_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un test del usuario.
    """
    test = crud_tests.get_test_by_id(db, test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test no encontrado"
        )
    
    if test.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este test"
        )
    
    crud_tests.delete_test(db, test_id)
    
    return None