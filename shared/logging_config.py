"""
Structured logging configuration
"""
import logging
import sys
import structlog
from pythonjsonlogger import jsonlogger


def configure_logging(service_name: str, log_level: str = "INFO"):
    """Configure structured logging with JSON output"""

    # Configure standard logging
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s',
        rename_fields={"levelname": "level", "asctime": "timestamp"}
    )
    log_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Add service name to all logs
    structlog.contextvars.bind_contextvars(service=service_name)

    return structlog.get_logger()
