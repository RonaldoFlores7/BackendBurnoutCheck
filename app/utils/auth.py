import bcrypt

def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        Hash de la contraseña como string
    """
    # Convertir a bytes y truncar a 72 bytes (límite de bcrypt)
    password_bytes = password.encode('utf-8')
    
    # Truncar si es necesario
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Generar salt y hashear
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Retornar como string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash.
    
    Args:
        plain_password: Contraseña en texto plano a verificar
        hashed_password: Hash almacenado en la base de datos
    
    Returns:
        True si la contraseña es correcta, False si no
    """
    # Convertir a bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Truncar si es necesario
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False