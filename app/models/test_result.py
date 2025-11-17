from app.database import Base
from sqlalchemy import Column, String, Integer, Enum, TIMESTAMP, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.enums import PredictionResult


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    prediction = Column(Enum(PredictionResult), nullable=False)
    probability = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    predicted_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relaciones
    test = relationship("Test", back_populates="result")
    recommendations = relationship("TestRecommendation", back_populates="test_result", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestResult {self.id} - Prediction: {self.prediction}>"