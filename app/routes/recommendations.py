from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User
from app.schemas.test_result import (
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationResponse
)
from app.dependencies import require_admin
from app.crud import recommendations as crud_recommendations


router = APIRouter()


# ==================== ADMIN ENDPOINTS ====================

@router.get("", response_model=List[RecommendationResponse])
def list_recommendations(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    for_positive_result: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Lista todas las recomendaciones con filtros.
    
    **Solo administradores.**
    
    Parámetros:
    - skip: Número de registros a saltar (paginación)
    - limit: Número máximo de registros a retornar
    - active_only: Si True, solo recomendaciones activas
    - for_positive_result: Si True, solo para "S". Si False, solo para "N". Si None, todas.
    """
    recommendations = crud_recommendations.get_all_recommendations(
        db, skip, limit, active_only, for_positive_result
    )
    return recommendations


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Obtiene una recomendación específica por ID.
    
    **Solo administradores.**
    """
    recommendation = crud_recommendations.get_recommendation_by_id(db, recommendation_id)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada"
        )
    
    return recommendation


@router.post("", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation(
    recommendation_data: RecommendationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Crea una nueva recomendación.
    
    **Solo administradores.**
    
    Ejemplo:
    ```json
    {
      "title": "Consulta con psicólogo",
      "description": "Te recomendamos agendar una cita con un profesional de salud mental.",
      "category": "Salud Mental",
      "for_positive_result": true,
      "active": true
    }
    ```
    
    - for_positive_result: true si es para predicción "S" (necesita ayuda)
    - for_positive_result: false si es para predicción "N" (está bien)
    """
    recommendation = crud_recommendations.create_recommendation(db, recommendation_data)
    return recommendation


@router.patch("/{recommendation_id}", response_model=RecommendationResponse)
def update_recommendation(
    recommendation_id: int,
    recommendation_update: RecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Actualiza una recomendación existente.
    
    **Solo administradores.**
    Solo actualiza los campos proporcionados.
    """
    recommendation = crud_recommendations.update_recommendation(
        db, recommendation_id, recommendation_update
    )
    return recommendation


@router.delete("/{recommendation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recommendation(
    recommendation_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Elimina o desactiva una recomendación.
    
    **Solo administradores.**
    
    - force=False (default): Desactiva la recomendación (soft delete) - RECOMENDADO
    - force=True: Elimina permanentemente la recomendación
    
    Nota: Si la recomendación ya está asignada a tests, usa soft delete (force=False).
    """
    if force:
        # Hard delete
        deleted = crud_recommendations.delete_recommendation(db, recommendation_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recomendación no encontrada"
            )
    else:
        # Soft delete (desactivar)
        crud_recommendations.deactivate_recommendation(db, recommendation_id)
    
    return None