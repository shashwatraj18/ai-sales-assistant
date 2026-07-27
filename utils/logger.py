"""
Centralized logging configuration.

Provides a single `get_logger(name)` factory so every module logs through
the same handler and formatter, controlled by `Settings.log_level`. Modules
should call this instead of `logging.basicConfig`, which only takes effect
on its first call - relying on it from multiple modules is a common source
of inconsistent logging setup.
"""

from __future__ import annotations

import logging
import sys

from utils.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root() -> None:
    """Configure the root logger exactly once, on first use."""
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(settings.log_level)
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring the root logger on first call.

    Usage:
        logger = get_logger(__name__)
        logger.info("Loaded %d rows", len(df))
    """
    _configure_root()
    return logging.getLogger(name)
