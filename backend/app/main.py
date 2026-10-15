from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth_router, analyses_router
from app.core.config import get_settings
from app.core.database import close_db, init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="AI-assisted reverse engineering workbench",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        https_only=settings.is_production,
        same_site="lax" if not settings.is_production else "strict",
        max_age=3600,
    )

    app.include_router(auth_router)
    app.include_router(analyses_router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "docs": "/docs" if settings.app_env != "production" else "disabled",
        }

    return app


app = create_app()