#!/usr/bin/env python3

import os
import sys
import unittest
from src.parser.state_machine_expander import StateMachineExpander, Tokenizer, TokenType, Token


class TestExpansionModifiers(unittest.TestCase):
    """Additional tests for parameter expansion modifiers"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a more extensive set of test variables
        self.variables = {
            "HOME": "/home/user",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "USER": "testuser",
            "count": "5",
            "empty": "",
            "zero": "0",
            "filename": "document.tar.gz",
            "multiword": "hello world",
            "uppercase": "HELLO",
            "lowercase": "hello",
            "mixedcase": "HeLLo",
            "path": "/usr/local/share/data",
            "url": "https://example.com/path/to/file.html?param=value",
            "comma_text": "hello,world,example",
            "spaces": "  leading and trailing spaces  ",
            "special_chars": "!@#$%^&*()",
            "numbers": "123456789",
        }
        
        def scope_provider(name):
            return self.variables.get(name)
        
        self.expander = StateMachineExpander(scope_provider)
        self.tokenizer = Tokenizer()
    
    def test_pattern_removal_multiple_matches(self):
        """Test pattern removal with multiple matches"""
        # Test shortest prefix removal with multiple matches
        result = self.expander.expand("${path#*/}")
        self.assertEqual(result, "local/share/data")
        
        # Test longest prefix removal with multiple matches  
        result = self.expander.expand("${path##*/}")
        self.assertEqual(result, "data")
    
    def test_pattern_removal_non_matching(self):
        """Test pattern removal with non-matching patterns"""
        # Test prefix pattern that doesn't match
        result = self.expander.expand("${filename#xyz}")
        self.assertEqual(result, "document.tar.gz")
        
        # Test suffix pattern that doesn't match
        result = self.expander.expand("${filename%xyz}")
        self.assertEqual(result, "document.tar.gz")
    
    def test_pattern_removal_with_wildcards(self):
        """Test pattern removal with different wildcard combinations"""
        # Test with ? wildcard for single character
        self.variables["text"] = "abcdef"
        result = self.expander.expand("${text#a?c}")
        self.assertEqual(result, "def")
        
        # Test with character classes
        self.variables["digits"] = "123abc"
        result = self.expander.expand("${digits#[0-9]*}")
        self.assertEqual(result, "abc")
    
    def test_complex_pattern_removal(self):
        """Test complex pattern removal scenarios"""
        # Remove protocol and domain from URL
        result = self.expander.expand("${url#https://}")
        self.assertEqual(result, "example.com/path/to/file.html?param=value")
        
        # Remove path from URL (longest match)
        result = self.expander.expand("${url##*/}")
        self.assertEqual(result, "file.html?param=value")
        
        # Remove query parameters from URL
        result = self.expander.expand(r"${url%\?*}")
        self.assertEqual(result, "https://example.com/path/to/file.html")
    
    def test_pattern_substitution_edge_cases(self):
        """Test pattern substitution edge cases"""
        # Test substitution with empty replacement
        result = self.expander.expand("${comma_text/,/}")
        self.assertEqual(result, "helloworld,example")
        
        # Test substitution with empty pattern
        self.variables["text"] = "sample"
        result = self.expander.expand("${text///_}")
        self.assertEqual(result, "sample")
        
        # Test global substitution
        result = self.expander.expand("${comma_text//,/-}")
        self.assertEqual(result, "hello-world-example")
        
        # Test substitution with special characters
        result = self.expander.expand(r"${special_chars/\$/X}")
        self.assertEqual(result, "!@#X%^&*()")
    
    def test_case_modification_edge_cases(self):
        """Test case modification edge cases"""
        # Test with empty string
        result = self.expander.expand("${empty^^}")
        self.assertEqual(result, "")
        
        # Test with numbers (should be unchanged)
        result = self.expander.expand("${numbers^^}")
        self.assertEqual(result, "123456789")
        
        # Test with special characters (should be unchanged)
        result = self.expander.expand("${special_chars^^}")
        self.assertEqual(result, "!@#$%^&*()")
        
        # Test with already uppercase
        result = self.expander.expand("${uppercase^^}")
        self.assertEqual(result, "HELLO")
        
        # Test with already lowercase
        result = self.expander.expand("${lowercase,,}")
        self.assertEqual(result, "hello")
    
    def test_string_length_edge_cases(self):
        """Test string length edge cases"""
        # Test length of empty string
        result = self.expander.expand("${#empty}")
        self.assertEqual(result, "0")
        
        # Test length of multiword string with spaces
        result = self.expander.expand("${#multiword}")
        self.assertEqual(result, "11")
        
        # Test length of string with special characters
        result = self.expander.expand("${#special_chars}")
        self.assertEqual(result, "10")
    
    def test_complex_nested_modifiers(self):
        """Test complex nested modifier combinations"""
        # Get filename without extension, then uppercase
        result = self.expander.expand("${${filename%%.*}^^}")
        self.assertEqual(result, "DOCUMENT")
        
        # Remove prefix, then lowercase
        self.variables["path"] = "/usr/local/bin"
        result = self.expander.expand("${${path##*/},,}")
        self.assertEqual(result, "bin")
        
        # Pattern substitution then case modification
        self.variables["text"] = "Hello-World"
        result = self.expander.expand("${${text/-/ }^^}")
        self.assertEqual(result, "HELLO WORLD")
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in parameter expansion"""
        # Trim leading spaces
        result = self.expander.expand("${spaces#  }")
        self.assertEqual(result, "leading and trailing spaces  ")
        
        # Trim trailing spaces
        result = self.expander.expand("${spaces%  }")
        self.assertEqual(result, "  leading and trailing spaces")
    
    def test_pattern_removal_with_dot_star(self):
        """Test specific patterns with .* that are common in scripts"""
        # Test various extensions
        self.variables["file1"] = "script.sh"
        self.variables["file2"] = "document.pdf"
        self.variables["file3"] = "image.tar.gz"
        
        # Remove extensions with %.*
        result = self.expander.expand("${file1%.*}")
        self.assertEqual(result, "script")
        
        result = self.expander.expand("${file2%.*}")
        self.assertEqual(result, "document")
        
        # Remove all extensions with %%.*
        result = self.expander.expand("${file3%%.*}")
        self.assertEqual(result, "image")
    
    def test_pattern_substitution_regex_behavior(self):
        """Test pattern substitution with regex-like patterns"""
        # Replace first occurrence of a digit
        result = self.expander.expand("${numbers/[0-9]/X}")
        self.assertEqual(result, "X23456789")
        
        # Replace all occurrences of digits
        result = self.expander.expand("${numbers//[0-9]/X}")
        self.assertEqual(result, "XXXXXXXXX")
    
    def test_combinations_of_modifiers(self):
        """Test applying multiple modifications in sequence through shell scripts"""
        # This replicates common shell idioms
        
        # Get base filename without extension, then make it lowercase
        self.variables["FILENAME"] = "Document.TXT"
        result = self.expander.expand("${${FILENAME%.*},,}")
        self.assertEqual(result, "document")
        
        # Extract domain from URL then uppercase it
        self.variables["url"] = "https://example.com/path"
        # Remove protocol prefix, then remove everything after domain
        domain_extraction = self.expander.expand("${${url#https://}%%/*}")
        self.assertEqual(domain_extraction, "example.com")
        # Now test uppercasing that result
        self.variables["domain"] = domain_extraction
        result = self.expander.expand("${domain^^}")
        self.assertEqual(result, "EXAMPLE.COM")


if __name__ == "__main__":
    unittest.main()