"""
app/core/logger.py
──────────────────
Structured logging configuration using structlog.
Supports both JSON (production) and coloured console (development) output.
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import get_settings


def _add_app_context(
    logger: WrappedLogger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """Inject static application context into every log record."""
    settings = get_settings()
    event_dict.setdefault("env", settings.app_env)
    event_dict.setdefault("app", "quant-engine")
    return event_dict


def configure_logging(
    log_level: str | None = None,
    log_format: str | None = None,
) -> None:
    """
    Configure structlog once at application startup.
    Call this function exactly once from main.py or test conftest.py.
    """
    settings = get_settings()
    level_name = log_level or settings.log_level
    format_name = log_format or settings.log_format
    level = getattr(logging, level_name.upper(), logging.INFO)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_app_context,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]

    if format_name.lower() == "json":
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a bound structlog logger for a given module name.

    Usage::

        log = get_logger(__name__)
        log.info("order.placed", order_id="OID-001", symbol="NIFTY")
    """
    return structlog.get_logger(name)  # type: ignore[return-value]


setup_logging = configure_logging
