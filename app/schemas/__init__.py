from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserChangePassword,
    UserResponse,
    UserDetailResponse,
)

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenRefresh,
    TokenResponse,
    TokenData,
)

from app.schemas.question import (
    QuestionOptionBase,
    QuestionOptionCreate,
    QuestionOptionResponse,
    QuestionBase,
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
)

from app.schemas.test import (
    TestBase,
    TestCreate,
    TestResponseSubmit,
    TestResponsesBatch,
    TestResponseDetail,
    TestResponse,
    TestDetailResponse,
    TestListResponse,
)

from app.schemas.test_result import (
    RecommendationBase,
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationResponse,
    TestResultBase,
    TestResultCreate,
    TestResultResponse,
    TestResultDetailResponse,
    MLPredictionRequest,
    MLPredictionResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserChangePassword",
    "UserResponse",
    "UserDetailResponse",
    
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenRefresh",
    "TokenResponse",
    "TokenData",
    
    # Question
    "QuestionOptionBase",
    "QuestionOptionCreate",
    "QuestionOptionResponse",
    "QuestionBase",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionListResponse",
    
    # Test
    "TestBase",
    "TestCreate",
    "TestResponseSubmit",
    "TestResponsesBatch",
    "TestResponseDetail",
    "TestResponse",
    "TestDetailResponse",
    "TestListResponse",
    
    # Test Result & Recommendations
    "RecommendationBase",
    "RecommendationCreate",
    "RecommendationUpdate",
    "RecommendationResponse",
    "TestResultBase",
    "TestResultCreate",
    "TestResultResponse",
    "TestResultDetailResponse",
    "MLPredictionRequest",
    "MLPredictionResponse",
]