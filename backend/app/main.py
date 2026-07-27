from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging on startup
import backend.app.core.logging as app_logging
from backend.app.api.routes import health
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
        version="0.1.0",
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

    return app


app = create_app()
