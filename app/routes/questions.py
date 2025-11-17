from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    QuestionOptionCreate,
    QuestionOptionResponse
)
from app.dependencies import require_admin, get_current_active_user
from app.crud import questions as crud_questions


router = APIRouter()


# ==================== ENDPOINTS PÚBLICOS/USUARIO ====================

@router.get("/active", response_model=List[QuestionResponse])
def get_active_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene todas las preguntas activas con sus opciones.
    
    Usado por el frontend para mostrar el cuestionario.
    Requiere usuario autenticado.
    """
    questions = crud_questions.get_active_questions(db)
    return questions


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene una pregunta específica por ID con sus opciones.
    """
    question = crud_questions.get_question_by_id(db, question_id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )
    
    return question


# ==================== ENDPOINTS ADMIN ====================

@router.get("", response_model=List[QuestionListResponse])
def list_all_questions(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Lista todas las preguntas (incluidas inactivas).
    
    **Solo administradores.**
    - skip: Número de registros a saltar (paginación)
    - limit: Número máximo de registros a retornar
    - active_only: Si True, solo muestra preguntas activas
    """
    questions = crud_questions.get_all_questions(db, skip, limit, active_only)
    return questions


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Crea una nueva pregunta con sus opciones.
    
    **Solo administradores.**
    
    Ejemplo:
    ```json
    {
      "question_key": "pregunta1",
      "question_text": "¿Con qué frecuencia te sientes agotado?",
      "category": "Agotamiento Emocional",
      "order": 1,
      "active": true,
      "options": [
        {"option_text": "Nunca", "option_value": "Nunca", "order": 1},
        {"option_text": "Rara vez", "option_value": "Rara vez", "order": 2},
        {"option_text": "A menudo", "option_value": "A menudo", "order": 3}
      ]
    }
    ```
    """
    question = crud_questions.create_question(db, question_data)
    return question


@router.patch("/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Actualiza una pregunta existente.
    
    **Solo administradores.**
    Solo actualiza los campos proporcionados.
    No actualiza las opciones (usar endpoints específicos de opciones).
    """
    question = crud_questions.update_question(db, question_id, question_update)
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Elimina o desactiva una pregunta.
    
    **Solo administradores.**
    
    - force=False (default): Desactiva la pregunta (soft delete) - RECOMENDADO
    - force=True: Elimina permanentemente la pregunta y sus opciones
    
    Nota: Si la pregunta tiene respuestas asociadas, usa soft delete (force=False).
    """
    if force:
        # Hard delete
        deleted = crud_questions.delete_question(db, question_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pregunta no encontrada"
            )
    else:
        # Soft delete (desactivar)
        crud_questions.deactivate_question(db, question_id)
    
    return None


# ==================== ENDPOINTS DE OPCIONES ====================

@router.post("/{question_id}/options", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
def add_question_option(
    question_id: int,
    option_data: QuestionOptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Agrega una nueva opción a una pregunta existente.
    
    **Solo administradores.**
    """
    option = crud_questions.create_question_option(db, question_id, option_data)
    return option


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question_option(
    option_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Elimina una opción de pregunta.
    
    **Solo administradores.**
    """
    deleted = crud_questions.delete_question_option(db, option_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opción no encontrada"
        )
    
    return None