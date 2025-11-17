from app.database import Base
from sqlalchemy import Column, String, Boolean, Integer, Text, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    for_positive_result = Column(Boolean, nullable=False, default=True)  # True="S", False="N"
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    test_recommendations = relationship("TestRecommendation", back_populates="recommendation")

    def __repr__(self):
        return f"<Recommendation {self.title}>"


class TestRecommendation(Base):
    """Tabla intermedia: qué recomendaciones se asignaron a cada resultado"""
    __tablename__ = "test_recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Constraint: No duplicar recomendaciones para un mismo resultado
    __table_args__ = (
        UniqueConstraint('test_result_id', 'recommendation_id', name='unique_test_recommendation'),
    )

    # Relaciones
    test_result = relationship("TestResult", back_populates="recommendations")
    recommendation = relationship("Recommendation", back_populates="test_recommendations")

    def __repr__(self):
        return f"<TestRecommendation Result:{self.test_result_id} Rec:{self.recommendation_id}>"