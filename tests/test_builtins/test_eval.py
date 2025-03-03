#!/usr/bin/env python3

import pytest
from unittest.mock import patch
from src.builtins.eval import eval_expr

def test_eval_basic():
    """Test basic eval functionality"""
    with patch('builtins.print') as mock_print:
        # Test simple expression
        eval_expr('2 + 2')
        mock_print.assert_called_once_with(4)
        
        # Test string expression
        mock_print.reset_mock()
        eval_expr('"hello" * 2')
        mock_print.assert_called_once_with('hellohello')

def test_eval_2_plus_2():
    """Test evaluating 2 + 2 specifically"""
    with patch('builtins.print') as mock_print:
        eval_expr('2', '+', '2')
        mock_print.assert_called_once_with(4)

def test_eval_multiple_args():
    """Test eval with multiple arguments"""
    with patch('builtins.print') as mock_print:
        # Test with multiple arguments
        eval_expr('1', '+', '1')
        mock_print.assert_called_once_with(2)

def test_eval_empty():
    """Test eval with no arguments"""
    with patch('builtins.print') as mock_print:
        # Test with no arguments
        eval_expr()
        mock_print.assert_not_called()

def test_eval_error():
    """Test eval error handling"""
    with patch('sys.stderr.write') as mock_stderr_write:
        # Test syntax error
        eval_expr('1 +')
        mock_stderr_write.assert_called()
        error_msg = ''.join(arg[0] for arg, _ in mock_stderr_write.call_args_list)
        assert 'invalid syntax' in error_msg
        
        # Test name error
        mock_stderr_write.reset_mock()
        eval_expr('undefined_var')
        mock_stderr_write.assert_called()
        error_msg = ''.join(arg[0] for arg, _ in mock_stderr_write.call_args_list)
        assert 'is not defined' in error_msg

def test_eval_none():
    """Test eval with expressions that return None"""
    with patch('builtins.print') as mock_print:
        # None results should not be printed
        eval_expr('None')
        mock_print.assert_not_called()

def test_eval_complex():
    """Test eval with complex expressions"""
    with patch('builtins.print') as mock_print:
        # Test list comprehension
        eval_expr('[x * 2 for x in range(3)]')
        mock_print.assert_called_once_with([0, 2, 4])
        
        # Test dictionary
        mock_print.reset_mock()
        eval_expr('{"a": 1, "b": 2}')
        mock_print.assert_called_once_with({'a': 1, 'b': 2})

def test_eval_builtins():
    """Test eval with built-in functions"""
    with patch('builtins.print') as mock_print:
        # Test len()
        eval_expr('len("test")')
        mock_print.assert_called_once_with(4)
        
        # Test abs()
        mock_print.reset_mock()
        eval_expr('abs(-42)')
        mock_print.assert_called_once_with(42)
