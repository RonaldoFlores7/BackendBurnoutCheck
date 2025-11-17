from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas.user import UserResponse, UserUpdate, UserChangePassword, UserDetailResponse
from app.utils.auth import hash_password, verify_password
from app.dependencies import get_current_active_user, require_admin


router = APIRouter()


@router.get("/me", response_model=UserDetailResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil del usuario autenticado actual.
    Incluye estadísticas de tests realizados.
    """
    # Contar tests del usuario
    from app.models import Test
    from app.models.enums import TestStatus
    
    total_tests = db.query(Test).filter(Test.user_id == current_user.id).count()
    completed_tests = db.query(Test).filter(
        Test.user_id == current_user.id,
        Test.status == TestStatus.COMPLETED
    ).count()
    
    # Crear respuesta con estadísticas
    user_data = UserDetailResponse.model_validate(current_user)
    user_data.total_tests = total_tests
    user_data.completed_tests = completed_tests
    
    return user_data


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el perfil del usuario autenticado.
    
    Solo se actualizan los campos proporcionados (partial update).
    No se puede cambiar el password aquí (usar /me/change-password).
    """
    # Verificar si intenta cambiar username a uno ya existente
    if user_update.username is not None and user_update.username != current_user.username:
        existing_user = db.query(User).filter(User.username == user_update.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso"
            )
        current_user.username = user_update.username
    
    # Verificar si intenta cambiar email a uno ya existente
    if user_update.email is not None and user_update.email != current_user.email:
        existing_email = db.query(User).filter(User.email == user_update.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )
        current_user.email = user_update.email
    
    # Actualizar otros campos si se proporcionan
    if user_update.name is not None:
        current_user.name = user_update.name
    
    if user_update.lastname is not None:
        current_user.lastname = user_update.lastname
    
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    
    # Los usuarios normales no pueden cambiar su propio role
    # Solo admins pueden hacerlo (ver endpoint de admin)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_my_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña del usuario autenticado.
    
    Requiere la contraseña actual para confirmar la identidad.
    """
    # Verificar contraseña actual
    if not verify_password(password_data.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )
    
    # Actualizar a nueva contraseña
    current_user.password = hash_password(password_data.new_password)
    
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente"}


# ==================== ADMIN ENDPOINTS ====================

@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Lista todos los usuarios del sistema.
    
    **Solo administradores.**
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Obtiene un usuario específico por ID.
    
    **Solo administradores.**
    """
    from app.models import Test
    from app.models.enums import TestStatus
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Contar tests del usuario
    total_tests = db.query(Test).filter(Test.user_id == user.id).count()
    completed_tests = db.query(Test).filter(
        Test.user_id == user.id,
        Test.status == TestStatus.COMPLETED
    ).count()
    
    user_data = UserDetailResponse.model_validate(user)
    user_data.total_tests = total_tests
    user_data.completed_tests = completed_tests
    
    return user_data


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Actualiza un usuario específico.
    
    **Solo administradores.** Pueden cambiar role y active.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Validar username único
    if user_update.username is not None and user_update.username != user.username:
        existing_user = db.query(User).filter(User.username == user_update.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso"
            )
        user.username = user_update.username
    
    # Validar email único
    if user_update.email is not None and user_update.email != user.email:
        existing_email = db.query(User).filter(User.email == user_update.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )
        user.email = user_update.email
    
    # Actualizar otros campos
    if user_update.name is not None:
        user.name = user_update.name
    
    if user_update.lastname is not None:
        user.lastname = user_update.lastname
    
    if user_update.phone is not None:
        user.phone = user_update.phone
    
    # Admins pueden cambiar role y active
    if user_update.role is not None:
        user.role = user_update.role
    
    if user_update.active is not None:
        user.active = user_update.active
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Elimina un usuario del sistema (hard delete).
    
    **Solo administradores.**
    Esto eliminará también todos sus tests por cascade.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # No permitir que un admin se elimine a sí mismo
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo"
        )
    
    db.delete(user)
    db.commit()
    
    return None