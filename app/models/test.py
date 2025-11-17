from app.database import Base
from sqlalchemy import Column, String, Integer, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.enums import TestStatus


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Datos demográficos del test
    ciclo = Column(Integer, nullable=False)
    genero = Column(String(50), nullable=False)
    facultad = Column(String(255), nullable=False)
    practicasprepro = Column(String(10), nullable=False)  # "Sí" o "No"
    
    # Control de estado
    status = Column(Enum(TestStatus), nullable=False, default=TestStatus.IN_PROGRESS)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relaciones
    user = relationship("User", back_populates="tests")
    responses = relationship("TestResponse", back_populates="test", cascade="all, delete-orphan")
    result = relationship("TestResult", back_populates="test", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Test {self.id} - User {self.user_id}>"