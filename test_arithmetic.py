#!/usr/bin/env python3

import os
import unittest
from src.parser.expander import expand_arithmetic
from src.parser.lexer import tokenize

class TestArithmeticExpansion(unittest.TestCase):
    
    def test_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        test_cases = [
            ('$((1 + 2))', '3'),
            ('$((10 - 5))', '5'),
            ('$((3 * 4))', '12'),
            ('$((20 / 5))', '4'),
            ('$((10 % 3))', '1'),
            ('$((2 ** 3))', '8'),
        ]
        
        for input_expr, expected in test_cases:
            self.assertEqual(expand_arithmetic(input_expr), expected)
    
    def test_variable_expansion(self):
        """Test arithmetic with variable expansion"""
        os.environ['X'] = '10'
        os.environ['Y'] = '5'
        
        test_cases = [
            ('$(($X + $Y))', '15'),
            ('$(($X * $Y))', '50'),
            ('$(($X / $Y))', '2'),
            # Non-existent variables should be treated as 0
            ('$(($Z + 5))', '5'),
        ]
        
        for input_expr, expected in test_cases:
            self.assertEqual(expand_arithmetic(input_expr), expected)
    
    def test_complex_expressions(self):
        """Test more complex arithmetic expressions"""
        test_cases = [
            ('$((1 + 2 * 3))', '7'),  # Operator precedence
            ('$(((1 + 2) * 3))', '9'),  # Parentheses
            ('$((10 > 5 ? 1 : 0))', '1'),  # Ternary operator
            ('$((10 < 5 ? 1 : 0))', '0'),
            ('$((1 && 1))', '1'),  # Logical operators
            ('$((1 || 0))', '1'),
            ('$((0 || 0))', '0'),
            ('$((!0))', '1'),
            ('$((!1))', '0'),
        ]
        
        for input_expr, expected in test_cases:
            self.assertEqual(expand_arithmetic(input_expr), expected)
            
    def test_nested_arithmetic(self):
        """Test nested arithmetic expressions"""
        from src.parser.expander import expand_all
        
        # Test nested arithmetic using expand_all
        test_case = '$((1 + $((2 * 3))))'
        self.assertEqual(expand_all(test_case), '7')
    
    def test_lexer_recognition(self):
        """Test that the lexer recognizes arithmetic expressions"""
        # Test that the lexer correctly identifies arithmetic tokens
        tokens = tokenize('echo $((1+2))')
        # Should be two tokens: 'echo' and '$((1+2))'
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[1].value, '$((1+2))')
        
    def test_integration_with_expand_all(self):
        """Test that arithmetic expansion works within expand_all"""
        from src.parser.expander import expand_all
        
        # Directly test arithmetic expansion in expand_all
        self.assertEqual(expand_all("$((1 + 2))"), "3")
        self.assertEqual(expand_all("The result is $(( 10 * 5 ))"), "The result is 50")
        
        # Test with shell execution style
        test_cases = [
            ('echo $((1 + 2))', 'echo 3'),
            # We need to account for how quotes are handled in expand_all
            ('echo "The result is $(( 10 * 5 ))"', 'echo The result is 50'),
        ]
        
        for input_cmd, expected in test_cases:
            # Process each token and expand
            tokens = tokenize(input_cmd)
            expanded_tokens = [expand_all(token.value) for token in tokens]
            result = ' '.join(expanded_tokens)
            self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()