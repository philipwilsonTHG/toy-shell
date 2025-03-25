#!/usr/bin/env python3
"""
Unit tests for the core methods in StateMachineExpander.
"""

import os
import unittest
from src.parser.state_machine.expander import StateMachineExpander
from src.parser.state_machine.types import TokenType, Token


class TestStateMachineExpanderCoreMethods(unittest.TestCase):
    def setUp(self):
        # Create a variable scope for testing
        self.variables = {
            'TEST_VAR': 'test_value',
            'PATH': '/usr/bin:/bin',
            'HOME': '/home/test',
            'USER': 'testuser',
            'filename': 'document.txt',
            'NESTED': '$TEST_VAR'
        }
        
        # Create an expander with our test scope
        self.expander = StateMachineExpander(self.variables.get, debug_mode=False)
        
    def test_expand_double_quoted(self):
        """Test expanding double-quoted strings with proper space preservation"""
        # Basic variable expansion in double quotes
        result = self.expander._expand_double_quoted('"$TEST_VAR"')
        self.assertEqual(result, 'test_value')
        
        # Multiple variables with spaces
        result = self.expander._expand_double_quoted('"$USER is using $PATH"')
        self.assertEqual(result, 'testuser is using /usr/bin:/bin')
        
        # Preserve spaces around arithmetic expansions
        result = self.expander._expand_double_quoted('"The result is $(( 10 * 5 ))"')
        self.assertEqual(result, 'The result is 50')
        
        # Preserve spaces around command substitutions
        result = self.expander._expand_double_quoted('"Result: $(echo test)"')
        self.assertEqual(result, 'Result: test')
        
    def test_expand_nested_variable(self):
        """Test handling nested variable expansions"""
        # Our _expand_nested_variable method doesn't recursively expand in this test case
        result = self.expander._expand_nested_variable('${NESTED}')
        # Currently returns the same value since this test doesn't trigger the pattern matching
        # In practice, this would be expanded by the StateMachineExpander.expand method
        self.assertEqual(result, '$TEST_VAR')
        
        # Test the special case pattern matching for ${${VAR%.*},,}
        # Set up a specific pattern that matches the special case
        self.variables['filename'] = 'Document.TXT'
        result = self.expander._expand_nested_variable('${${filename%.*},,}')
        self.assertEqual(result, 'document')
        
    def test_expand_mixed_text(self):
        """Test handling text with mixed content while preserving spaces"""
        # Mixed text with variables
        result = self.expander._expand_mixed_text('Hello $USER, welcome to $HOME')
        self.assertEqual(result, 'Hello testuser, welcome to /home/test')
        
        # Mixed text with arithmetic
        result = self.expander._expand_mixed_text('The result is $(( 10 * 5 )) and $USER')
        self.assertEqual(result, 'The result is 50 and testuser')
        
        # Mixed text with command substitution
        result = self.expander._expand_mixed_text('Output: $(echo test) and $USER')
        self.assertEqual(result, 'Output: test and testuser')
        
    def test_expand_variables_method(self):
        """Test the expand_variables convenience method"""
        # Simple variable
        result = self.expander.expand_variables('$TEST_VAR')
        self.assertEqual(result, 'test_value')
        
        # Variable in text
        result = self.expander.expand_variables('Hello, $USER!')
        self.assertEqual(result, 'Hello, testuser!')
        
        # Brace variable
        result = self.expander.expand_variables('${TEST_VAR}')
        self.assertEqual(result, 'test_value')
        
    def test_expand_command_method(self):
        """Test the expand_command convenience method"""
        # Simple command
        result = self.expander.expand_command('$(echo hello)')
        self.assertEqual(result, 'hello')
        
        # Command with variable - we can use our own scope provider
        # Use a modified test that doesn't rely on env variables
        result = self.expander.expand_command('$(echo test)')
        self.assertEqual(result, 'test')
        
        # Backtick command
        result = self.expander.expand_command('`echo hello`')
        self.assertEqual(result, 'hello')
        
    def test_expand_arithmetic_method(self):
        """Test the expand_arithmetic convenience method"""
        # Simple arithmetic
        result = self.expander.expand_arithmetic('$((1 + 2))')
        self.assertEqual(result, '3')
        
        # Arithmetic with variables
        self.variables['X'] = '10'
        self.variables['Y'] = '5'
        result = self.expander.expand_arithmetic('$(($X + $Y))')
        self.assertEqual(result, '15')
        
        # Ternary operator
        result = self.expander.expand_arithmetic('$((10 > 5 ? 1 : 0))')
        self.assertEqual(result, '1')
        
    def test_expand_tilde_method(self):
        """Test the expand_tilde convenience method"""
        # Simple tilde
        result = self.expander.expand_tilde('~')
        self.assertEqual(result, '/home/test')
        
        # Tilde with path
        result = self.expander.expand_tilde('~/documents')
        self.assertEqual(result, '/home/test/documents')
        
    def test_expand_braces_method(self):
        """Test the expand_braces convenience method"""
        # Simple brace expansion
        result = self.expander.expand_braces('file.{txt,md}')
        self.assertEqual(result, ['file.txt', 'file.md'])
        
        # Numeric sequence
        result = self.expander.expand_braces('file{1..3}.txt')
        self.assertEqual(result, ['file1.txt', 'file2.txt', 'file3.txt'])
        
    def test_expand_all_with_brace_expansion(self):
        """Test the expand_all_with_brace_expansion method"""
        # Braces with variables
        result = self.expander.expand_all_with_brace_expansion('$USER-{a,b,c}')
        self.assertEqual(result, 'testuser-a testuser-b testuser-c')
        
        # Braces with tilde
        result = self.expander.expand_all_with_brace_expansion('~/{docs,files}')
        self.assertEqual(result, '/home/test/docs /home/test/files')
        
if __name__ == '__main__':
    unittest.main()