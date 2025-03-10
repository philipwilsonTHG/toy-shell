#!/usr/bin/env python3
"""
Tests for the POSIX test builtin command implementation.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from io import StringIO

from src.builtins.test import test_command as shell_test_command

class TestBuiltinTest(unittest.TestCase):
    """Test cases for the test command and [ command."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary file for file tests
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.write(b"test content")
        self.temp_file.close()
        
        # Create a temporary directory for directory tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Create an empty file for size tests
        self.empty_file = tempfile.NamedTemporaryFile(delete=False)
        self.empty_file.close()
    
    def tearDown(self):
        """Clean up test environment."""
        os.unlink(self.temp_file.name)
        os.unlink(self.empty_file.name)
        os.rmdir(self.temp_dir)
    
    def test_no_arguments(self):
        """Test with no arguments."""
        # test with no arguments should return false (1)
        self.assertEqual(shell_test_command(), 1)
        
        # [ with just closing bracket should return false (1)
        self.assertEqual(shell_test_command('[', ']'), 1)
    
    def test_bracket_syntax(self):
        """Test bracket syntax requirements."""
        # Missing closing bracket should error
        with patch('sys.stderr', new=StringIO()) as fake_stderr:
            self.assertEqual(shell_test_command('[', 'true'), 2)
            self.assertIn("missing ']'", fake_stderr.getvalue())
    
    def test_single_argument(self):
        """Test with a single argument."""
        # Non-empty string should return true (0)
        self.assertEqual(shell_test_command('hello'), 0)
        
        # Empty string should return false (1)
        self.assertEqual(shell_test_command(''), 1)
    
    def test_file_operators(self):
        """Test file operators."""
        # -e (file exists)
        self.assertEqual(shell_test_command('-e', self.temp_file.name), 0)
        self.assertEqual(shell_test_command('-e', '/nonexistent/file'), 1)
        
        # -f (regular file)
        self.assertEqual(shell_test_command('-f', self.temp_file.name), 0)
        self.assertEqual(shell_test_command('-f', self.temp_dir), 1)
        
        # -d (directory)
        self.assertEqual(shell_test_command('-d', self.temp_dir), 0)
        self.assertEqual(shell_test_command('-d', self.temp_file.name), 1)
        
        # -s (non-empty file)
        self.assertEqual(shell_test_command('-s', self.temp_file.name), 0)
        self.assertEqual(shell_test_command('-s', self.empty_file.name), 1)
        
    def test_string_operators(self):
        """Test string operators."""
        # -z (zero length)
        self.assertEqual(shell_test_command('-z', ''), 0)
        self.assertEqual(shell_test_command('-z', 'hello'), 1)
        
        # -n (non-zero length)
        self.assertEqual(shell_test_command('-n', 'hello'), 0)
        self.assertEqual(shell_test_command('-n', ''), 1)
        
        # String equality
        self.assertEqual(shell_test_command('abc', '=', 'abc'), 0)
        self.assertEqual(shell_test_command('abc', '=', 'def'), 1)
        
        # String inequality
        self.assertEqual(shell_test_command('abc', '!=', 'def'), 0)
        self.assertEqual(shell_test_command('abc', '!=', 'abc'), 1)
    
    def test_integer_operators(self):
        """Test integer comparison operators."""
        # -eq (equal)
        self.assertEqual(shell_test_command('5', '-eq', '5'), 0)
        self.assertEqual(shell_test_command('5', '-eq', '10'), 1)
        
        # -ne (not equal)
        self.assertEqual(shell_test_command('5', '-ne', '10'), 0)
        self.assertEqual(shell_test_command('5', '-ne', '5'), 1)
        
        # -gt (greater than)
        self.assertEqual(shell_test_command('10', '-gt', '5'), 0)
        self.assertEqual(shell_test_command('5', '-gt', '10'), 1)
        self.assertEqual(shell_test_command('5', '-gt', '5'), 1)
        
        # -ge (greater than or equal)
        self.assertEqual(shell_test_command('10', '-ge', '5'), 0)
        self.assertEqual(shell_test_command('5', '-ge', '5'), 0)
        self.assertEqual(shell_test_command('3', '-ge', '5'), 1)
        
        # -lt (less than)
        self.assertEqual(shell_test_command('5', '-lt', '10'), 0)
        self.assertEqual(shell_test_command('10', '-lt', '5'), 1)
        self.assertEqual(shell_test_command('5', '-lt', '5'), 1)
        
        # -le (less than or equal)
        self.assertEqual(shell_test_command('5', '-le', '10'), 0)
        self.assertEqual(shell_test_command('5', '-le', '5'), 0)
        self.assertEqual(shell_test_command('10', '-le', '5'), 1)
        
        # Invalid integer
        with patch('sys.stderr', new=StringIO()) as fake_stderr:
            self.assertEqual(shell_test_command('abc', '-eq', '5'), 2)
            self.assertIn("integer expression expected", fake_stderr.getvalue())
    
    def test_logical_operators(self):
        """Test logical operators."""
        # Negation
        self.assertEqual(shell_test_command('!', ''), 0)
        self.assertEqual(shell_test_command('!', 'hello'), 1)
        
        # AND
        self.assertEqual(shell_test_command('hello', '-a', 'world'), 0)
        self.assertEqual(shell_test_command('hello', '-a', ''), 1)
        self.assertEqual(shell_test_command('', '-a', 'world'), 1)
        
        # OR
        self.assertEqual(shell_test_command('hello', '-o', 'world'), 0)
        self.assertEqual(shell_test_command('hello', '-o', ''), 0)
        self.assertEqual(shell_test_command('', '-o', 'world'), 0)
        self.assertEqual(shell_test_command('', '-o', ''), 1)
        
        # Complex expressions
        self.assertEqual(shell_test_command('!', '(', 'hello', '-a', 'world', ')'), 1)
        self.assertEqual(shell_test_command('(', 'hello', '-o', '', ')', '-a', 'world'), 0)
        self.assertEqual(shell_test_command('(', 'hello', '-o', '', ')', '-a', ''), 1)
    
    def test_complex_expressions(self):
        """Test more complex expressions."""
        # Test file exists AND has content OR is a directory
        self.assertEqual(
            shell_test_command(
                '(', '-e', self.temp_file.name, '-a', '-s', self.temp_file.name, ')',
                '-o',
                '(', '-d', self.temp_dir, ')'
            ), 
            0
        )
        
        # Test negation of complex expression
        self.assertEqual(
            shell_test_command(
                '!',
                '(', 
                '(', '-e', '/nonexistent/file', ')',
                '-o',
                '(', '5', '-gt', '10', ')',
                ')'
            ),
            0
        )
    
    def test_error_handling(self):
        """Test error handling."""
        # Unknown unary operator
        with patch('sys.stderr', new=StringIO()) as fake_stderr:
            self.assertEqual(shell_test_command('-q', 'file'), 2)
            self.assertIn("unknown unary operator", fake_stderr.getvalue())
        
        # Unknown binary operator
        with patch('sys.stderr', new=StringIO()) as fake_stderr:
            self.assertEqual(shell_test_command('5', '-unknown', '10'), 2)
            self.assertIn("unknown binary operator", fake_stderr.getvalue())
        
        # Invalid expression
        with patch('sys.stderr', new=StringIO()) as fake_stderr:
            self.assertEqual(shell_test_command('a', 'b', 'c', 'd'), 2)
            self.assertIn("invalid test expression", fake_stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
# Add a comment
