"""Basic tests to verify pytest infrastructure"""
import pytest


def test_pytest_infrastructure():
    """Verify pytest is working correctly"""
    assert True


def test_basic_assertion():
    """Basic test to ensure pytest is working"""
    assert 1 + 1 == 2


def test_string_operations():
    """Test basic Python string operations"""
    test_str = "Hello World"
    assert test_str.lower() == "hello world"
    assert test_str.upper() == "HELLO WORLD"
    assert len(test_str) == 11


def test_list_operations():
    """Test basic Python list operations"""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert sum(test_list) == 15
    assert max(test_list) == 5
    assert min(test_list) == 1

