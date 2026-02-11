"""Logging utilities for RAGKIT Desktop."""

import collections
import logging
from datetime import datetime
from typing import Any

# Global buffer to store recent logs
LOG_BUFFER: collections.deque[dict[str, Any]] = collections.deque(maxlen=1000)


class ListHandler(logging.Handler):
    """Logging handler that stores logs in a memory buffer."""

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Format exception if present
            if record.exc_info and not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            
            entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "line": record.lineno,
                "exception": record.exc_text
            }
            LOG_BUFFER.append(entry)
        except Exception:
            self.handleError(record)


def setup_log_capture(level: int = logging.INFO) -> None:
    """Configure and attach the memory log handler."""
    handler = ListHandler(level)
    # Add to root logger to capture everything
    logging.getLogger().addHandler(handler)
    
    # Also ensure ragkit logger captures it (though root should cover it)
    # logging.getLogger("ragkit").addHandler(handler)
