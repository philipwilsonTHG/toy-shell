#!/usr/bin/env python3
"""
Brace expansion compatibility tests that compare psh behavior with bash.

These tests verify that psh's brace expansion produces the same output as bash.
"""

import pytest
from .framework import ShellCompatibilityTester, create_compatibility_test


class TestBraceExpansion:
    """Test brace expansion compatibility between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_basic_expansion(self):
        """Test basic brace expansion with comma-separated values."""
        self.tester.assert_outputs_match("""
        echo {a,b,c}
        """)
        
    def test_prefix_suffix(self):
        """Test brace expansion with prefix and suffix."""
        self.tester.assert_outputs_match("""
        echo pre{d,l,n}post
        """)
    
    def test_nested_braces(self):
        """Test nested brace expansion."""
        self.tester.assert_outputs_match("""
        echo {a,b{1,2,3},c}
        """)
    
    def test_numeric_range(self):
        """Test numeric range expansion."""
        self.tester.assert_outputs_match("""
        echo {1..5}
        """)
        
    def test_reverse_numeric_range(self):
        """Test reverse numeric range expansion."""
        self.tester.assert_outputs_match("""
        echo {5..1}
        """)
    
    def test_alphabetic_range(self):
        """Test alphabetic range expansion."""
        self.tester.assert_outputs_match("""
        echo {a..e}
        """)
        
    def test_reverse_alphabetic_range(self):
        """Test reverse alphabetic range expansion."""
        self.tester.assert_outputs_match("""
        echo {e..a}
        """)
    
    def test_uppercase_alphabetic_range(self):
        """Test uppercase alphabetic range expansion."""
        self.tester.assert_outputs_match("""
        echo {A..E}
        """)
    
    def test_quoting(self):
        """Test quoting in brace expansion."""
        self.tester.assert_outputs_match("""
        echo '{a,b,c}'
        echo "{a,b,c}"
        """)
    
    def test_escaped_braces(self):
        """Test escaped braces."""
        self.tester.assert_outputs_match(r"""
        echo \{a,b,c\}
        """)
    
    def test_variable_in_braces(self):
        """Test variables inside brace expansion."""
        self.tester.assert_outputs_match("""
        A=foo
        B=bar
        echo {$A,$B}
        """)
    
    def test_multiple_brace_expansions(self):
        """Test multiple brace expansions in one command."""
        self.tester.assert_outputs_match("""
        echo {a,b}_{1,2}
        """)
        
    def test_combined_patterns(self):
        """Test combined patterns with ranges and lists."""
        self.tester.assert_outputs_match("""
        echo file{1..3}.{txt,log}
        """)
        
        self.tester.assert_outputs_match("""
        echo {1..3}{a..c}
        """)
    
    def test_empty_elements(self):
        """Test brace expansion with empty elements."""
        self.tester.assert_outputs_match("""
        echo a{,b,c}d
        """)
    
    def test_single_element(self):
        """Test brace with a single element (no expansion)."""
        self.tester.assert_outputs_match("""
        echo {abc}
        """)
    
    def test_with_spaces(self):
        """Test brace expansion with spaces."""
        self.tester.assert_outputs_match("""
        echo { a , b , c }
        """)
    
    def test_complex_mixed_expansion(self):
        """Test complex mixed brace expansion patterns."""
        self.tester.assert_outputs_match("""
        echo /usr/{local/{bin,lib},bin}
        """)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])