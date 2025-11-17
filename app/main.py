from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

# Models
from app.models import user, question, enums, recommendation, test_response, test_result, test

# Routes
from app.routes import auth, users, questions, recommendations, tests

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

@app.get("/")
async def root():
    return {
        "message": "API",
        "version": settings.APP_VERSION,
        "status": "running"
    }

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(tests.router, prefix="/api/v1/tests", tags=["Tests"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
