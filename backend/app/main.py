from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging on startup
import backend.app.core.logging as app_logging
from backend.app.api.routes import health
from backend.app.api.routes import products as products_router
from backend.app.api.routes import reviews as reviews_router
from backend.app.api.routes import insights as insights_router
from backend.app.api.routes import chat as chat_router
from backend.app.auth import router as auth_router
from backend.app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    app_logging.logger.info(
        "Starting BrandGuard API Server...",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )
    yield
    # Shutdown actions
    app_logging.logger.info("Stopping BrandGuard API Server...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="BrandGuard API",
        description="AI-Powered Review Intelligence Hub API",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict this in production settings
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(health.router, prefix="/api/v1", tags=["healthcheck"])
    app.include_router(auth_router.router, prefix="/api/v1", tags=["auth"])
    app.include_router(products_router.router, prefix="/api/v1", tags=["products"])
    app.include_router(reviews_router.router, prefix="/api/v1", tags=["reviews"])
    app.include_router(insights_router.router, prefix="/api/v1", tags=["insights"])
    app.include_router(chat_router.router, prefix="/api/v1", tags=["ask-brandguard"])

    return app


app = create_app()
