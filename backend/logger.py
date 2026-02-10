"""
Centralized logging module with session tracking for debugging.
Provides structured logging with session IDs to trace requests across the system.
"""
import logging
import uuid
import json
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional
from functools import wraps

# Context variables for session and request IDs (async/context-safe)
_session_id: ContextVar[str] = ContextVar('session_id', default='no-session')
_request_id: ContextVar[str] = ContextVar('request_id', default='no-request')


def get_session_id() -> str:
    """Get the current session ID from context."""
    return _session_id.get()


def set_session_id(session_id: str) -> None:
    """Set the current session ID in context."""
    _session_id.set(session_id)


def get_request_id() -> str:
    """Get the current request ID from context."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Set the current request ID in context."""
    _request_id.set(request_id)


def generate_session_id() -> str:
    """Generate a new unique session ID."""
    return str(uuid.uuid4())[:8]


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())[:8]


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    Includes session ID, request ID, timestamp, and other metadata.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Get session and request IDs from context
        session_id = get_session_id()
        request_id = get_request_id()
        
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "session_id": session_id,
            "request_id": request_id,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data
            
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)


class ReadableFormatter(logging.Formatter):
    """
    Human-readable formatter with session/request ID prefix.
    Useful for development and local debugging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        session_id = get_session_id()
        request_id = get_request_id()
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        # Format: [timestamp] [level] [session:request] module.function:line - message
        prefix = f"[{timestamp}] [{record.levelname:8}] [{session_id}:{request_id}]"
        location = f"{record.module}.{record.funcName}:{record.lineno}"
        
        formatted = f"{prefix} {location} - {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
            
        return formatted


def setup_logger(
    name: str = "ai_batake",
    level: int = logging.INFO,
    use_json: bool = False
) -> logging.Logger:
    """
    Set up and configure the application logger.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        use_json: If True, use JSON format; otherwise use readable format
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Choose formatter based on preference
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = ReadableFormatter()
        
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger


# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Get the global logger instance, creating it if necessary."""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def log_with_context(
    level: int,
    message: str,
    extra_data: Optional[dict] = None,
    exc_info: bool = False
) -> None:
    """
    Log a message with the current session/request context.
    
    Args:
        level: Logging level
        message: Log message
        extra_data: Optional dictionary of additional data to include
        exc_info: Whether to include exception info
    """
    logger = get_logger()
    
    # Create a custom LogRecord with extra data
    record = logger.makeRecord(
        logger.name,
        level,
        "",  # pathname will be filled by caller info
        0,   # lineno will be filled by caller info
        message,
        (),
        exc_info=exc_info if exc_info else None
    )
    
    if extra_data:
        record.extra_data = extra_data
        
    logger.handle(record)


# Convenience functions for different log levels
def debug(message: str, **kwargs) -> None:
    """Log debug message with context."""
    logger = get_logger()
    logger.debug(message, **kwargs)


def info(message: str, **kwargs) -> None:
    """Log info message with context."""
    logger = get_logger()
    logger.info(message, **kwargs)


def warning(message: str, **kwargs) -> None:
    """Log warning message with context."""
    logger = get_logger()
    logger.warning(message, **kwargs)


def error(message: str, exc_info: bool = False, **kwargs) -> None:
    """Log error message with context."""
    logger = get_logger()
    logger.error(message, exc_info=exc_info, **kwargs)


def critical(message: str, exc_info: bool = False, **kwargs) -> None:
    """Log critical message with context."""
    logger = get_logger()
    logger.critical(message, exc_info=exc_info, **kwargs)


def log_function_call(func):
    """
    Decorator to log function entry and exit with timing.
    Useful for tracing execution flow.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        start_time = datetime.now(timezone.utc)
        
        debug(f"ENTER {func_name}")
        
        try:
            result = func(*args, **kwargs)
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            debug(f"EXIT {func_name} (took {elapsed:.2f}ms)")
            return result
        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            error(f"EXCEPTION in {func_name} (after {elapsed:.2f}ms): {str(e)}", exc_info=True)
            raise
            
    return wrapper


def log_async_function_call(func):
    """
    Decorator to log async function entry and exit with timing.
    Useful for tracing execution flow in async functions.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        start_time = datetime.now(timezone.utc)
        
        debug(f"ENTER (async) {func_name}")
        
        try:
            result = await func(*args, **kwargs)
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            debug(f"EXIT (async) {func_name} (took {elapsed:.2f}ms)")
            return result
        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            error(f"EXCEPTION in (async) {func_name} (after {elapsed:.2f}ms): {str(e)}", exc_info=True)
            raise
            
    return wrapper
