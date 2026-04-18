"""Configure the root logger: level from LOG_LEVEL, text or JSON format (LOG_FORMAT)."""

from __future__ import annotations

import logging
import sys

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    from pythonjsonlogger.jsonlogger import JsonFormatter

from app.core.settings import settings
from app.middleware.request_id import request_id_ctx


class RequestIdFilter(logging.Filter):
    """Attach request_id from the contextvar to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def setup_logging() -> None:
    """Call once per process after environment variables are loaded."""
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    fmt = settings.log_format.strip().lower()
    if fmt == "json":
        formatter = JsonFormatter(
            "%(levelname)s %(name)s %(message)s %(request_id)s",
            rename_fields={"levelname": "level"},
        )
    else:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s")

    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
