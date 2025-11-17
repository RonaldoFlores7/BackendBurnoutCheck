from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.recommendation import Recommendation
from app.schemas.test_result import RecommendationCreate, RecommendationUpdate


def get_recommendation_by_id(db: Session, recommendation_id: int) -> Optional[Recommendation]:
    """Obtiene una recomendación por ID"""
    return db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()


def get_all_recommendations(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = False,
    for_positive_result: Optional[bool] = None
) -> List[Recommendation]:
    """
    Obtiene todas las recomendaciones con filtros.
    
    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros
        active_only: Si True, solo recomendaciones activas
        for_positive_result: Si True, solo para "S". Si False, solo para "N". Si None, todas.
    """
    query = db.query(Recommendation)
    
    if active_only:
        query = query.filter(Recommendation.active == True)
    
    if for_positive_result is not None:
        query = query.filter(Recommendation.for_positive_result == for_positive_result)
    
    return query.order_by(Recommendation.created_at.desc()).offset(skip).limit(limit).all()


def get_active_recommendations(db: Session, for_positive_result: bool) -> List[Recommendation]:
    """
    Obtiene recomendaciones activas según el tipo de predicción.
    
    Args:
        for_positive_result: True para predicción "S", False para "N"
    """
    return db.query(Recommendation).filter(
        Recommendation.active == True,
        Recommendation.for_positive_result == for_positive_result
    ).all()


def create_recommendation(db: Session, recommendation_data: RecommendationCreate) -> Recommendation:
    """Crea una nueva recomendación"""
    new_recommendation = Recommendation(
        title=recommendation_data.title,
        description=recommendation_data.description,
        category=recommendation_data.category,
        for_positive_result=recommendation_data.for_positive_result,
        active=recommendation_data.active
    )
    
    db.add(new_recommendation)
    db.commit()
    db.refresh(new_recommendation)
    
    return new_recommendation


def update_recommendation(
    db: Session, 
    recommendation_id: int, 
    recommendation_update: RecommendationUpdate
) -> Recommendation:
    """
    Actualiza una recomendación existente.
    Solo actualiza los campos proporcionados.
    """
    recommendation = get_recommendation_by_id(db, recommendation_id)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada"
        )
    
    # Actualizar campos proporcionados
    if recommendation_update.title is not None:
        recommendation.title = recommendation_update.title
    
    if recommendation_update.description is not None:
        recommendation.description = recommendation_update.description
    
    if recommendation_update.category is not None:
        recommendation.category = recommendation_update.category
    
    if recommendation_update.for_positive_result is not None:
        recommendation.for_positive_result = recommendation_update.for_positive_result
    
    if recommendation_update.active is not None:
        recommendation.active = recommendation_update.active
    
    db.commit()
    db.refresh(recommendation)
    
    return recommendation


def delete_recommendation(db: Session, recommendation_id: int) -> bool:
    """
    Elimina una recomendación permanentemente.
    Retorna True si se eliminó, False si no existía.
    """
    recommendation = get_recommendation_by_id(db, recommendation_id)
    
    if not recommendation:
        return False
    
    db.delete(recommendation)
    db.commit()
    
    return True


def deactivate_recommendation(db: Session, recommendation_id: int) -> Recommendation:
    """
    Desactiva una recomendación en lugar de eliminarla (soft delete).
    Recomendado si ya está asignada a resultados de tests.
    """
    recommendation = get_recommendation_by_id(db, recommendation_id)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada"
        )
    
    recommendation.active = False
    db.commit()
    db.refresh(recommendation)
    
    return recommendation