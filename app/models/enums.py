import enum

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class TestStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PredictionResult(str, enum.Enum):
    S = "SI"  # Sí necesita recomendaciones
    N = "N"  # No necesita recomendaciones