from app.database import Base
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class TestResponse(Base):
    __tablename__ = "test_responses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    answer_value = Column(String(100), nullable=False)
    answered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Constraint: Una pregunta solo se puede responder una vez por test
    __table_args__ = (
        UniqueConstraint('test_id', 'question_id', name='unique_test_question'),
    )

    # Relaciones
    test = relationship("Test", back_populates="responses")
    question = relationship("Question", back_populates="responses")

    def __repr__(self):
        return f"<TestResponse Test:{self.test_id} Q:{self.question_id}>"