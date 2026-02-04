"""Tests for logger.py module"""
import pytest
import sys
import os
from unittest.mock import patch

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
    
    def test_info_log(self, capfd):
        """Test info logging"""
        set_session_id("test-session")
        set_request_id("test-request")
        info("Test info message")
        # Just verify no exception is raised
    
    def test_debug_log(self, capfd):
        """Test debug logging"""
        set_session_id("debug-session")
        set_request_id("debug-request")
        debug("Test debug message")
        # Just verify no exception is raised
    
    def test_warning_log(self, capfd):
        """Test warning logging"""
        set_session_id("warn-session")
        set_request_id("warn-request")
        warning("Test warning message")
        # Just verify no exception is raised
    
    def test_error_log(self, capfd):
        """Test error logging"""
        set_session_id("error-session")
        set_request_id("error-request")
        error("Test error message")
        # Just verify no exception is raised
    
    def test_error_log_with_exc_info(self, capfd):
        """Test error logging with exception info"""
        set_session_id("exc-session")
        set_request_id("exc-request")
        try:
            raise ValueError("Test exception")
        except ValueError:
            error("Test error with exception", exc_info=True)
        # Just verify no exception is raised


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
