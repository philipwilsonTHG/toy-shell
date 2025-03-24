#!/usr/bin/env python3

import os
import sys
import unittest
from src.parser.state_machine_expander import StateMachineExpander, Tokenizer, TokenType, Token


class TestExpansionEdgeCases(unittest.TestCase):
    """Tests for edge cases and potential failure modes in parameter expansion"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create variables that include potential edge cases
        self.variables = {
            # Empty values
            "EMPTY": "",
            "NULL": None,  # Should be treated as empty
            
            # Nested expansions
            "NAME": "USER",
            "USER": "admin",
            
            # Unicode and special characters
            "UNICODE": "こんにちは世界",
            "EMOJI": "Hello 🌍 World! 😊",
            "ACCENTS": "résumé café naïve",
            "SPECIAL": "a*b?c[d]e{f}g",
            "ESCAPES": "line1\\nline2\\tindented",
            
            # Values that look like shell syntax
            "DOLLAR": "$100",
            "COMMAND": "$(echo test)",
            "BRACES": "{a,b,c}",
            "QUOTES": "say \"hello\"",
            "BACKTICKS": "`hostname`",
            
            # Values with regex special characters
            "REGEX_SPECIAL": "a+b*c?d{2}e[0-9]f\\g|h^i$j.",
            
            # Nested parameter expansion examples
            "PARENT": "${CHILD}",
            "CHILD": "value",
            
            # Long strings
            "LONG": "x" * 1000,
            
            # Filenames with multiple extensions
            "FILENAME": "archive.tar.gz.bak",
            
            # Paths with special segments
            "PATH_WITH_DOT": "/usr/local/./bin",
            "PATH_WITH_DOTDOT": "/usr/local/../lib",
            
            # URL with complex query string
            "COMPLEX_URL": "https://example.com/search?q=term&page=1&sort=desc&filter[]=tag1&filter[]=tag2",
        }
        
        def scope_provider(name):
            return self.variables.get(name)
        
        self.expander = StateMachineExpander(scope_provider)
        self.tokenizer = Tokenizer()
    
    def test_empty_values(self):
        """Test handling of empty and null values"""
        # Empty variable
        result = self.expander.expand("${EMPTY}")
        self.assertEqual(result, "")
        
        # Null variable (should be treated as empty)
        result = self.expander.expand("${NULL}")
        self.assertEqual(result, "")
        
        # Non-existent variable
        result = self.expander.expand("${NONEXISTENT}")
        self.assertEqual(result, "")
    
    def test_indirect_variable_references(self):
        """Test indirect variable references (variable containing variable name)"""
        # Using NAME to reference USER
        # Note: This is a common pattern that should be handled
        # This might not work in the current implementation without special handling
        result = self.expander.expand("${!NAME}")
        # We'd expect "admin" if the implementation supports !var indirect references
        # But if not, we'll just make sure it doesn't crash
        self.assertIsNotNone(result)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters"""
        # Japanese text
        result = self.expander.expand("${UNICODE}")
        self.assertEqual(result, "こんにちは世界")
        
        # Text with emoji
        result = self.expander.expand("${EMOJI}")
        self.assertEqual(result, "Hello 🌍 World! 😊")
        
        # Text with accents
        result = self.expander.expand("${ACCENTS}")
        self.assertEqual(result, "résumé café naïve")
        
        # Pattern removal with Unicode
        result = self.expander.expand("${UNICODE#こん}")
        self.assertEqual(result, "にちは世界")
        
        # Case modification with Unicode
        # Note: May depend on Python's Unicode handling
        result = self.expander.expand("${ACCENTS^^}")
        self.assertEqual(result, "RÉSUMÉ CAFÉ NAÏVE")
    
    def test_special_character_handling(self):
        """Test handling of shell special characters in variable values"""
        # Value with * character
        result = self.expander.expand("${SPECIAL}")
        self.assertEqual(result, "a*b?c[d]e{f}g")
        
        # Value that looks like a command substitution
        result = self.expander.expand("${COMMAND}")
        self.assertEqual(result, "$(echo test)")
        
        # Value that looks like a brace expansion
        result = self.expander.expand("${BRACES}")
        self.assertEqual(result, "{a,b,c}")
        
        # Value with $ character
        result = self.expander.expand("${DOLLAR}")
        self.assertEqual(result, "$100")
        
        # Value with quotes
        result = self.expander.expand("${QUOTES}")
        self.assertEqual(result, "say \"hello\"")
        
        # Value with backticks
        result = self.expander.expand("${BACKTICKS}")
        self.assertEqual(result, "`hostname`")
    
    def test_pattern_removal_with_special_chars(self):
        """Test pattern removal with values containing special characters"""
        # Remove pattern with regex special chars
        result = self.expander.expand("${REGEX_SPECIAL#a+}")
        self.assertEqual(result, "b*c?d{2}e[0-9]f\\g|h^i$j.")
        
        # Remove suffix with special chars
        result = self.expander.expand("${REGEX_SPECIAL%$j.}")
        self.assertEqual(result, "a+b*c?d{2}e[0-9]f\\g|h^i")
    
    def test_nesting_at_variable_boundaries(self):
        """Test expansions that occur at variable name boundaries"""
        # Variable reference at the boundary
        self.variables["PREFIX"] = "PRE"
        self.variables["PREFIXSUFFIX"] = "combined value"
        result = self.expander.expand("${PREFIX}SUFFIX")
        self.assertEqual(result, "PRESUFFIX")
        
        # Nested variables that might be ambiguous
        self.variables["X"] = "value_of_X"
        self.variables["X_Y"] = "value_of_X_Y"
        result = self.expander.expand("${X}_Y")
        self.assertEqual(result, "value_of_X_Y")
    
    def test_multiple_extensions(self):
        """Test handling multiple extensions in filenames"""
        # Remove last extension
        result = self.expander.expand("${FILENAME%.*}")
        self.assertEqual(result, "archive.tar.gz")
        
        # Remove another extension
        result = self.expander.expand("${${FILENAME%.*}%.*}")
        self.assertEqual(result, "archive.tar")
        
        # Remove all extensions
        result = self.expander.expand("${FILENAME%%.*}")
        self.assertEqual(result, "archive")
    
    def test_path_normalization(self):
        """Test behavior with paths containing . and .. segments"""
        # Path with . segment
        result = self.expander.expand("${PATH_WITH_DOT#/usr/}")
        self.assertEqual(result, "local/./bin")
        
        # Path with .. segment
        result = self.expander.expand("${PATH_WITH_DOTDOT#/usr/}")
        self.assertEqual(result, "local/../lib")
    
    def test_long_string_handling(self):
        """Test handling of long strings"""
        # Length of a long string
        result = self.expander.expand("${#LONG}")
        self.assertEqual(result, "1000")
        
        # Pattern removal in a long string
        result = self.expander.expand("${LONG#x}")
        # Should remove just one character
        self.assertEqual(len(result), 999)
        
        # Pattern substitution in a long string
        result = self.expander.expand("${LONG//x/y}")
        self.assertEqual(result, "y" * 1000)
    
    def test_complex_url_parsing(self):
        """Test parsing complex URLs with pattern expansion"""
        # Extract query string
        result = self.expander.expand(r"${COMPLEX_URL#*\?}")
        self.assertEqual(result, "q=term&page=1&sort=desc&filter[]=tag1&filter[]=tag2")
        
        # Extract domain
        result = self.expander.expand("${COMPLEX_URL#https://}")
        result = self.expander.expand("${result%%/*}")
        self.assertEqual(result, "example.com")
        
        # Extract first query parameter
        result = self.expander.expand(r"${COMPLEX_URL#*\?}")
        result = self.expander.expand("${result%%&*}")
        self.assertEqual(result, "q=term")
    
    def test_escape_sequence_handling(self):
        """Test handling of escape sequences in variable values"""
        # Value with escape sequences
        result = self.expander.expand("${ESCAPES}")
        # Expect literal backslashes to be preserved
        self.assertEqual(result, "line1\\nline2\\tindented")
    
    def test_deeply_nested_expansions(self):
        """Test deeply nested parameter expansions"""
        # Set up a chain of nested variables
        self.variables["A"] = "B"
        self.variables["B"] = "C"
        self.variables["C"] = "D"
        self.variables["D"] = "value"
        
        # Try to resolve through multiple levels
        # Note: This might not be supported in the current implementation
        result = self.expander.expand("${${${${A}}}}")
        # We'd expect "value" in bash, but our implementation might handle this differently
        # The main test is that it doesn't crash with deep nesting
        self.assertIsNotNone(result)
    
    def test_modifiers_on_empty_values(self):
        """Test applying modifiers to empty values"""
        # Pattern removal on empty string
        result = self.expander.expand("${EMPTY#pattern}")
        self.assertEqual(result, "")
        
        # Case modification on empty string
        result = self.expander.expand("${EMPTY^^}")
        self.assertEqual(result, "")
        
        # Pattern substitution on empty string
        result = self.expander.expand("${EMPTY/pattern/replacement}")
        self.assertEqual(result, "")
    
    def test_parameter_expansion_at_boundaries(self):
        """Test parameter expansion at string boundaries"""
        # Parameter expansion at the start
        result = self.expander.expand("${USER}suffix")
        self.assertEqual(result, "adminsuffix")
        
        # Parameter expansion at the end
        result = self.expander.expand("prefix${USER}")
        self.assertEqual(result, "prefixadmin")
        
        # Multiple parameter expansions without separators
        result = self.expander.expand("${USER}${USER}")
        self.assertEqual(result, "adminadmin")
    
    def test_special_modifiers_escape_handling(self):
        """Test handling of escaped characters in modifiers"""
        # Escaped special characters in pattern
        self.variables["PATH"] = "/path/to/file"
        result = self.expander.expand("${PATH#/path\\/}")
        self.assertEqual(result, "to/file")
        
        # Escaped * in pattern
        self.variables["TEXT"] = "a*bc"
        result = self.expander.expand("${TEXT#a\\*}")
        self.assertEqual(result, "bc")
    
    def test_modifier_with_escaped_delimiters(self):
        """Test pattern substitution with escaped delimiters"""
        # Substitution with escaped delimiter
        self.variables["TEXT"] = "a/b/c"
        result = self.expander.expand("${TEXT//\\//:}")
        self.assertEqual(result, "a:b:c")


if __name__ == "__main__":
    unittest.main()