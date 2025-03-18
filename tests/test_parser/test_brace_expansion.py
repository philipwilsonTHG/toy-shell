#!/usr/bin/env python3
"""
Tests for brace expansion functionality.
"""

import pytest
from src.parser.brace_expander import expand_braces


class TestBraceExpansion:
    """Test the brace expansion implementation."""
    
    def test_basic_expansion(self):
        """Test basic brace expansion with comma-separated patterns."""
        assert expand_braces("echo {a,b,c}") == ["echo a", "echo b", "echo c"]
        assert expand_braces("{foo,bar,baz}") == ["foo", "bar", "baz"]
    
    def test_prefix_suffix(self):
        """Test brace expansion with prefix and suffix."""
        assert expand_braces("pre{d,l,n}post") == ["predpost", "prelpost", "prenpost"]
    
    def test_no_expansion_needed(self):
        """Test text that doesn't need expansion."""
        assert expand_braces("no braces here") == ["no braces here"]
        assert expand_braces("{}") == ["{}"]  # Empty braces should not expand
        assert expand_braces("{single}") == ["{single}"]  # Single item no commas
    
    def test_numeric_range_expansion(self):
        """Test numeric range expansion."""
        assert expand_braces("{1..5}") == ["1", "2", "3", "4", "5"]
        assert expand_braces("{5..1}") == ["5", "4", "3", "2", "1"]
        assert expand_braces("file{1..3}.txt") == ["file1.txt", "file2.txt", "file3.txt"]
        
    def test_range_with_step(self):
        """Test range expansion with step/increment."""
        # Numeric ranges with step
        assert expand_braces("{1..10..2}") == ["1", "3", "5", "7", "9"]
        assert expand_braces("{10..1..2}") == ["10", "8", "6", "4", "2"]
        assert expand_braces("{1..10..3}") == ["1", "4", "7", "10"]
        
        # Alphabetic ranges with step
        assert expand_braces("{a..m..3}") == ["a", "d", "g", "j", "m"]
        assert expand_braces("{Z..A..5}") == ["Z", "U", "P", "K", "F", "A"]
        
        # Ranges with prefixes and suffixes
        assert expand_braces("file{1..7..2}.txt") == ["file1.txt", "file3.txt", "file5.txt", "file7.txt"]
    
    def test_alphabetic_range_expansion(self):
        """Test alphabetic range expansion."""
        assert expand_braces("{a..e}") == ["a", "b", "c", "d", "e"]
        assert expand_braces("{e..a}") == ["e", "d", "c", "b", "a"]
        assert expand_braces("{A..E}") == ["A", "B", "C", "D", "E"]
    
    def test_nested_braces(self):
        """Test nested brace expansion."""
        assert expand_braces("{a,b{1,2,3},c}") == ["a", "b1", "b2", "b3", "c"]
        assert expand_braces("X{a,{b,c}d}Y") == ["XaY", "XbdY", "XcdY"]
    
    def test_multiple_brace_patterns(self):
        """Test multiple brace patterns in one string."""
        assert expand_braces("{a,b}_{1,2}") == ["a_1", "a_2", "b_1", "b_2"]
        
    def test_combined_patterns(self):
        """Test combined patterns with ranges and lists."""
        assert expand_braces("file{1..3}.{txt,log}") == [
            "file1.txt", "file1.log", 
            "file2.txt", "file2.log", 
            "file3.txt", "file3.log"
        ]
        assert expand_braces("img{1..2}.{png,jpg}") == [
            "img1.png", "img1.jpg", 
            "img2.png", "img2.jpg"
        ]
    
    def test_quotes_handling(self):
        """Test brace expansion quote handling according to POSIX rules."""
        # Single quotes prevent brace expansion
        assert expand_braces("'{a,b,c}'") == ["'{a,b,c}'"]
        
        # Double quotes should still allow brace expansion
        assert expand_braces('"{a,b,c}"') == ['"a"', '"b"', '"c"']
        
        # Mixed quotes
        assert expand_braces("'single'{a,b}'quote'") == ["'single'a'quote'", "'single'b'quote'"]
    
    def test_escaped_braces(self):
        """Test that escaped braces don't expand."""
        assert expand_braces(r"\{a,b,c\}") == [r"\{a,b,c\}"]
    
    def test_empty_elements(self):
        """Test brace expansion with empty elements."""
        assert expand_braces("a{,b,c}d") == ["ad", "abd", "acd"]
        assert expand_braces("{foo,,bar}") == ["foo", "", "bar"]
    
    def test_complex_path_expansion(self):
        """Test complex path expansion."""
        expected = [
            "/usr/local/bin", 
            "/usr/local/lib", 
            "/usr/bin"
        ]
        assert expand_braces("/usr/{local/{bin,lib},bin}") == expected
    
    def test_with_spaces(self):
        """Test that spaces around commas are preserved in the result."""
        assert expand_braces("{ a , b , c }") == [" a ", " b ", " c "]
        
    def test_variable_expansion_interaction(self):
        """Test how brace expansion interacts with variable expansion."""
        # This test requires manual setup since expand_braces doesn't 
        # handle variable expansion directly - it's part of the shell's
        # expansion pipeline.
        
        # In the shell, brace expansion happens before variable expansion,
        # so variables passed directly to expand_braces won't be expanded.
        # This is handled properly in the integration tests.
        assert expand_braces("{$A,$B}") == ["$A", "$B"]
        assert expand_braces("prefix{$A,$B}suffix") == ["prefix$Asuffix", "prefix$Bsuffix"]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])