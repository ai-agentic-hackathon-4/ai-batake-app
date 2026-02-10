"""Tests for logger.py module"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import (
    generate_session_id, generate_request_id,
    set_session_id, set_request_id, get_session_id, get_request_id,
    get_logger, setup_logger, info, debug, warning, error
)


class TestSessionManagement:
    """Tests for session and request ID management"""
    
    def test_generate_session_id_unique(self):
        """Test that generated session IDs are unique"""
        ids = [generate_session_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All should be unique
    
    def test_generate_session_id_format(self):
        """Test session ID format (8 characters)"""
        session_id = generate_session_id()
        assert len(session_id) == 8
    
    def test_generate_request_id_unique(self):
        """Test that generated request IDs are unique"""
        ids = [generate_request_id() for _ in range(100)]
        assert len(set(ids)) == 100
    
    def test_set_and_get_session_id(self):
        """Test setting and getting session ID"""
        test_id = "test-session-123"
        set_session_id(test_id)
        assert get_session_id() == test_id
    
    def test_set_and_get_request_id(self):
        """Test setting and getting request ID"""
        test_id = "test-request-456"
        set_request_id(test_id)
        assert get_request_id() == test_id
    
    def test_default_session_id_value(self):
        """Test that session ID defaults are reasonable strings"""
        # The default is 'no-session' for session_id and 'no-request' for request_id
        # We test that the functions return strings
        session = get_session_id()
        request = get_request_id()
        assert isinstance(session, str)
        assert isinstance(request, str)
        assert len(session) > 0
        assert len(request) > 0


class TestLoggerSetup:
    """Tests for logger setup and configuration"""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance"""
        import logging
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
    
    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance"""
        import logging
        logger = setup_logger(name="test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_logger_singleton(self):
        """Test that get_logger returns the same instance"""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2


class TestLogFunctions:
    """Tests for log helper functions"""
    
    def test_info_log_does_not_raise(self):
        """Test info logging executes without error"""
        set_session_id("test-session")
        set_request_id("test-request")
        # Should not raise any exception
        info("Test info message")
    
    def test_debug_log_does_not_raise(self):
        """Test debug logging executes without error"""
        set_session_id("debug-session")
        set_request_id("debug-request")
        debug("Test debug message")
    
    def test_warning_log_does_not_raise(self):
        """Test warning logging executes without error"""
        set_session_id("warn-session")
        set_request_id("warn-request")
        warning("Test warning message")
    
    def test_error_log_does_not_raise(self):
        """Test error logging executes without error"""
        set_session_id("error-session")
        set_request_id("error-request")
        error("Test error message")
    
    def test_error_log_with_exc_info_does_not_raise(self):
        """Test error logging with exc_info captures exception without raising"""
        set_session_id("exc-session")
        set_request_id("exc-request")
        try:
            raise ValueError("Test exception")
        except ValueError:
            error("Test error with exception", exc_info=True)


class TestSessionTracking:
    """Tests for session tracking across function calls"""
    
    def test_session_context_preservation(self):
        """Test that session context is preserved"""
        original_session = "original-session"
        original_request = "original-request"
        
        set_session_id(original_session)
        set_request_id(original_request)
        
        # Simulate nested function call
        def inner_function():
            return get_session_id(), get_request_id()
        
        session, request = inner_function()
        assert session == original_session
        assert request == original_request
    
    def test_session_change_within_function(self):
        """Test that session can be changed within a function"""
        set_session_id("first-session")
        set_request_id("first-request")
        
        # Change session in nested call
        def change_session():
            set_session_id("second-session")
            set_request_id("second-request")
            return get_session_id(), get_request_id()
        
        session, request = change_session()
        assert session == "second-session"
        assert request == "second-request"


# ---------------------------------------------------------------------------
# Additional tests for 100% coverage
# ---------------------------------------------------------------------------
import logging
import json
import asyncio
from unittest.mock import patch, Mock, MagicMock
import pytest

from logger import (
    StructuredFormatter,
    ReadableFormatter,
    log_with_context,
    critical,
    log_function_call,
    log_async_function_call,
)


class TestStructuredFormatterFormat:
    """Tests for StructuredFormatter.format() method (lines 57-80)."""

    def test_format_returns_valid_json(self):
        """Test that format() produces valid JSON output."""
        set_session_id("fmt-session")
        set_request_id("fmt-request")

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test_file.py",
            lineno=10,
            msg="hello world",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["session_id"] == "fmt-session"
        assert parsed["request_id"] == "fmt-request"
        assert parsed["message"] == "hello world"
        assert "timestamp" in parsed
        assert "module" in parsed
        assert "function" in parsed
        assert "line" in parsed

    def test_format_includes_extra_data(self):
        """Test that extra_data is included in JSON output when present."""
        set_session_id("extra-s")
        set_request_id("extra-r")

        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test_file.py",
            lineno=20,
            msg="with data",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value"}

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["data"] == {"key": "value"}

    def test_format_includes_exception_info(self):
        """Test that exception info is included when exc_info is set."""
        formatter = StructuredFormatter()

        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test_file.py",
            lineno=30,
            msg="error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "exception" in parsed
        assert "RuntimeError" in parsed["exception"]
        assert "boom" in parsed["exception"]

    def test_format_without_extra_data_or_exception(self):
        """Test format output when neither extra_data nor exc_info is present."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test_file.py",
            lineno=40,
            msg="plain message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "data" not in parsed
        assert "exception" not in parsed


class TestSetupLoggerJsonBranch:
    """Tests for setup_logger() with use_json=True (line 138)."""

    def test_setup_logger_with_json_formatter(self):
        """Test that use_json=True configures StructuredFormatter."""
        # Use a unique name to avoid handler-already-exists guard
        logger = setup_logger(name="test_json_formatter_branch", use_json=True)
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, StructuredFormatter)

        # Cleanup
        logger.handlers.clear()


class TestLogWithContext:
    """Tests for log_with_context() function (lines 178-194)."""

    def test_log_with_context_basic(self):
        """Test log_with_context logs a message at the given level."""
        import logger as logger_mod

        with patch.object(logger_mod, "_logger", None):
            log_with_context(logging.INFO, "context message")

    def test_log_with_context_extra_data(self):
        """Test log_with_context attaches extra_data to the record."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.name = "mock"

        # makeRecord should return a real-ish record that we can inspect
        real_record = logging.LogRecord(
            name="mock", level=logging.INFO,
            pathname="", lineno=0,
            msg="ctx msg", args=(), exc_info=None,
        )
        mock_logger.makeRecord.return_value = real_record

        with patch.object(logger_mod, "_logger", mock_logger):
            log_with_context(logging.INFO, "ctx msg", extra_data={"a": 1})

        assert hasattr(real_record, "extra_data")
        assert real_record.extra_data == {"a": 1}
        mock_logger.handle.assert_called_once_with(real_record)

    def test_log_with_context_exc_info(self):
        """Test log_with_context passes exc_info correctly."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.name = "mock"

        real_record = logging.LogRecord(
            name="mock", level=logging.ERROR,
            pathname="", lineno=0,
            msg="error", args=(), exc_info=None,
        )
        mock_logger.makeRecord.return_value = real_record

        with patch.object(logger_mod, "_logger", mock_logger):
            log_with_context(logging.ERROR, "error", exc_info=True)

        # makeRecord should have been called with exc_info=True (positional or keyword)
        call_args = mock_logger.makeRecord.call_args
        positional = call_args[0]
        keyword = call_args[1]
        # exc_info is passed as keyword arg 'exc_info' or as positional arg
        exc_info_value = keyword.get("exc_info", None)
        if exc_info_value is None and len(positional) > 6:
            exc_info_value = positional[6]
        assert exc_info_value is True

    def test_log_with_context_no_extra_data(self):
        """Test log_with_context without extra_data does not set attribute."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.name = "mock"

        real_record = logging.LogRecord(
            name="mock", level=logging.INFO,
            pathname="", lineno=0,
            msg="no extra", args=(), exc_info=None,
        )
        mock_logger.makeRecord.return_value = real_record

        with patch.object(logger_mod, "_logger", mock_logger):
            log_with_context(logging.INFO, "no extra")

        assert not hasattr(real_record, "extra_data")


class TestCriticalFunction:
    """Tests for critical() convenience function (lines 224-225)."""

    def test_critical_calls_logger_critical(self):
        """Test that critical() delegates to logger.critical()."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)

        with patch.object(logger_mod, "_logger", mock_logger):
            critical("critical message")

        mock_logger.critical.assert_called_once_with("critical message", exc_info=False)

    def test_critical_with_exc_info(self):
        """Test that critical() passes exc_info when set to True."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)

        with patch.object(logger_mod, "_logger", mock_logger):
            critical("critical with exc", exc_info=True)

        mock_logger.critical.assert_called_once_with("critical with exc", exc_info=True)


class TestLogFunctionCallDecorator:
    """Tests for log_function_call() decorator (lines 233-250)."""

    def test_decorator_returns_result(self):
        """Test that decorated function returns correct result."""
        @log_function_call
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_decorator_preserves_function_name(self):
        """Test that @wraps preserves function metadata."""
        @log_function_call
        def my_func():
            pass

        assert my_func.__name__ == "my_func"

    def test_decorator_logs_entry_and_exit(self):
        """Test that decorator logs ENTER and EXIT messages."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.level = logging.DEBUG
        mock_logger.isEnabledFor.return_value = True

        with patch.object(logger_mod, "_logger", mock_logger):
            @log_function_call
            def sample():
                return 42

            sample()

        # debug is called for ENTER and EXIT
        assert mock_logger.debug.call_count >= 2

    def test_decorator_logs_exception_and_reraises(self):
        """Test that decorator logs exception and re-raises it."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.level = logging.DEBUG
        mock_logger.isEnabledFor.return_value = True

        with patch.object(logger_mod, "_logger", mock_logger):
            @log_function_call
            def fail():
                raise ValueError("test error")

            with pytest.raises(ValueError, match="test error"):
                fail()

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "EXCEPTION" in call_args[0][0]


class TestLogAsyncFunctionCallDecorator:
    """Tests for log_async_function_call() decorator (lines 258-275)."""

    @pytest.mark.asyncio
    async def test_async_decorator_returns_result(self):
        """Test that async decorated function returns correct result."""
        @log_async_function_call
        async def async_add(a, b):
            return a + b

        result = await async_add(3, 4)
        assert result == 7

    @pytest.mark.asyncio
    async def test_async_decorator_preserves_function_name(self):
        """Test that @wraps preserves async function metadata."""
        @log_async_function_call
        async def my_async_func():
            pass

        assert my_async_func.__name__ == "my_async_func"

    @pytest.mark.asyncio
    async def test_async_decorator_logs_entry_and_exit(self):
        """Test that async decorator logs ENTER and EXIT messages."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.level = logging.DEBUG
        mock_logger.isEnabledFor.return_value = True

        with patch.object(logger_mod, "_logger", mock_logger):
            @log_async_function_call
            async def async_sample():
                return 99

            await async_sample()

        assert mock_logger.debug.call_count >= 2

    @pytest.mark.asyncio
    async def test_async_decorator_logs_exception_and_reraises(self):
        """Test that async decorator logs exception and re-raises it."""
        import logger as logger_mod

        mock_logger = MagicMock(spec=logging.Logger)
        mock_logger.level = logging.DEBUG
        mock_logger.isEnabledFor.return_value = True

        with patch.object(logger_mod, "_logger", mock_logger):
            @log_async_function_call
            async def async_fail():
                raise RuntimeError("async error")

            with pytest.raises(RuntimeError, match="async error"):
                await async_fail()

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "EXCEPTION" in call_args[0][0]
