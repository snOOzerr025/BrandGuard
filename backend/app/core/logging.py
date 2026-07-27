import logging
import sys

import structlog

from backend.app.core.config import settings


def setup_logging():
    """Configure structured logging using structlog"""
    # Standard library logging config
    logging_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Processors shared between structlog and standard logging
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.ENVIRONMENT == "production":
        # JSON formatting for production/structured logs
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Colorful dev console logs
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure root standard library logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=(
                structlog.dev.ConsoleRenderer(colors=True)
                if settings.ENVIRONMENT != "production"
                else structlog.processors.JSONRenderer()
            ),
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging_level)

    # Disable generic logging noise if not in DEBUG mode
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


# Setup logs on import
setup_logging()
logger = structlog.get_logger("brandguard")
