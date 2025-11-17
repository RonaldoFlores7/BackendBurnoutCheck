from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.question import Question, QuestionOption
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionOptionCreate


def get_question_by_id(db: Session, question_id: int) -> Optional[Question]:
    """Obtiene una pregunta por ID"""
    return db.query(Question).filter(Question.id == question_id).first()


def get_question_by_key(db: Session, question_key: str) -> Optional[Question]:
    """Obtiene una pregunta por su key (ej: 'pregunta1')"""
    return db.query(Question).filter(Question.question_key == question_key).first()


def get_all_questions(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Question]:
    """
    Obtiene todas las preguntas con paginación.
    Si active_only=True, solo retorna preguntas activas.
    """
    query = db.query(Question)
    
    if active_only:
        query = query.filter(Question.active == True)
    
    return query.order_by(Question.order).offset(skip).limit(limit).all()


def get_active_questions(db: Session) -> List[Question]:
    """Obtiene solo las preguntas activas ordenadas"""
    return db.query(Question).filter(Question.active == True).order_by(Question.order).all()


def create_question(db: Session, question_data: QuestionCreate) -> Question:
    """
    Crea una nueva pregunta con sus opciones.
    Valida que el question_key sea único.
    """
    # Verificar que no exista ya ese question_key
    existing = get_question_by_key(db, question_data.question_key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una pregunta con el key '{question_data.question_key}'"
        )
    
    # Crear pregunta
    new_question = Question(
        question_key=question_data.question_key,
        question_text=question_data.question_text,
        category=question_data.category,
        order=question_data.order,
        active=question_data.active
    )
    
    db.add(new_question)
    db.flush()  # Para obtener el ID sin hacer commit
    
    # Crear opciones
    for option_data in question_data.options:
        new_option = QuestionOption(
            question_id=new_question.id,
            option_text=option_data.option_text,
            option_value=option_data.option_value,
            order=option_data.order
        )
        db.add(new_option)
    
    db.commit()
    db.refresh(new_question)
    
    return new_question


def update_question(db: Session, question_id: int, question_update: QuestionUpdate) -> Question:
    """
    Actualiza una pregunta existente.
    Solo actualiza los campos proporcionados.
    """
    question = get_question_by_id(db, question_id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )
    
    # Actualizar campos proporcionados
    if question_update.question_text is not None:
        question.question_text = question_update.question_text
    
    if question_update.category is not None:
        question.category = question_update.category
    
    if question_update.order is not None:
        question.order = question_update.order
    
    if question_update.active is not None:
        question.active = question_update.active
    
    db.commit()
    db.refresh(question)
    
    return question


def delete_question(db: Session, question_id: int) -> bool:
    """
    Elimina una pregunta y sus opciones (cascade).
    Retorna True si se eliminó, False si no existía.
    """
    question = get_question_by_id(db, question_id)
    
    if not question:
        return False
    
    db.delete(question)
    db.commit()
    
    return True


def deactivate_question(db: Session, question_id: int) -> Question:
    """
    Desactiva una pregunta en lugar de eliminarla (soft delete).
    Recomendado si ya tiene respuestas asociadas.
    """
    question = get_question_by_id(db, question_id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )
    
    question.active = False
    db.commit()
    db.refresh(question)
    
    return question


def create_question_option(db: Session, question_id: int, option_data: QuestionOptionCreate) -> QuestionOption:
    """Agrega una nueva opción a una pregunta existente"""
    question = get_question_by_id(db, question_id)
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pregunta no encontrada"
        )
    
    new_option = QuestionOption(
        question_id=question_id,
        option_text=option_data.option_text,
        option_value=option_data.option_value,
        order=option_data.order
    )
    
    db.add(new_option)
    db.commit()
    db.refresh(new_option)
    
    return new_option


def delete_question_option(db: Session, option_id: int) -> bool:
    """Elimina una opción de pregunta"""
    option = db.query(QuestionOption).filter(QuestionOption.id == option_id).first()
    
    if not option:
        return False
    
    db.delete(option)
    db.commit()
    
    return True