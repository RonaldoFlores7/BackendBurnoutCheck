from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.utils.auth import hash_password, verify_password
from app.utils.jwt import create_access_token
from app.config import settings


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema.
    
    - **username**: Nombre de usuario único (3-50 caracteres)
    - **email**: Correo electrónico único
    - **password**: Contraseña (mínimo 8 caracteres)
    
    Retorna el usuario creado sin el password.
    """
    # Verificar si el username ya existe
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )
    
    # Verificar si el email ya existe
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    # Crear nuevo usuario
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password=hash_password(user_data.password),
        role=UserRole.USER,  # Por defecto es USER
        name="",  # Se completará después en editar perfil
        lastname="",
        phone="",
        active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autentica un usuario y retorna un token JWT.
    
    - **username**: Nombre de usuario
    - **password**: Contraseña
    
    Retorna un access_token para usar en requests autenticados.
    """
    # Buscar usuario por username
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta al administrador"
        )
    
    # Crear token JWT
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value
        }
    )
    
    # Calcular tiempo de expiración (si está configurado)
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0 else None
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in
    )