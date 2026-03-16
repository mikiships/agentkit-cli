"""Tests for the sample main module."""
from src.main import add, greet, fibonacci


def test_add():
    assert add(2, 3) == 5


def test_greet():
    assert greet("World") == "Hello, World!"


def test_fibonacci():
    assert fibonacci(10) == 55
