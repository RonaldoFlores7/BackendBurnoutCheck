from app.database import Base
from sqlalchemy import Column, String, Boolean, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_key = Column(String(50), unique=True, nullable=False, index=True)  # ej: "pregunta1"
    question_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    order = Column(Integer, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    responses = relationship("TestResponse", back_populates="question")

    def __repr__(self):
        return f"<Question {self.question_key}>"


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_text = Column(String(100), nullable=False)
    option_value = Column(String(100), nullable=False)
    order = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relaciones
    question = relationship("Question", back_populates="options")

    def __repr__(self):
        return f"<QuestionOption {self.option_text}>"