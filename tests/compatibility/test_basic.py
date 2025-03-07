#!/usr/bin/env python3
"""
Basic compatibility tests that compare psh behavior with bash.

These tests verify that psh produces the same output as bash for
standard shell commands and features.
"""

import os
import tempfile
import pytest
from .framework import ShellCompatibilityTester, create_compatibility_test


class TestBasicCommands:
    """Test basic shell command compatibility between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_echo_command(self):
        """Test basic echo command."""
        self.tester.assert_outputs_match("echo 'Hello, World!'")
    
    def test_variable_expansion(self):
        """Test variable expansion."""
        # Use environment variable directly for more stable test
        cmd = """
        export MSG='Hello'
        echo $MSG
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_command_substitution(self):
        """Test command substitution."""
        self.tester.assert_outputs_match("echo $(echo 'nested command')")
    
    def test_exit_status(self):
        """Test exit status handling."""
        self.tester.assert_outputs_match("""
        true
        echo $?
        """)
        self.tester.assert_outputs_match("""
        false
        echo $?
        """)
    
    def test_pipe_simple(self):
        """Test simple pipeline."""
        self.tester.assert_outputs_match("echo 'hello' | cat")


class TestQuoting:
    """Test quoting behavior between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_single_quotes(self):
        """Test single quote handling."""
        # Use a separate command for more stable testing
        self.tester.assert_outputs_match("""
        echo 'Single quotes: $HOME'
        """)
    
    def test_double_quotes(self):
        """Test double quote handling."""
        self.tester.assert_outputs_match("echo \"Double quotes: $HOME\"")
    
    def test_escaped_chars(self):
        """Test escaped character handling."""
        # Use raw string to avoid Python escape warning
        self.tester.assert_outputs_match(r"""
        echo "Escaped: \$HOME"
        """)
    
    def test_mixed_quotes(self):
        """Test mixed quote handling."""
        cmd = """echo "Mixed 'quotes' in string" """
        self.tester.assert_outputs_match(cmd)


class TestRedirection:
    """Test redirection compatibility between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_output_redirection(self):
        """Test output redirection."""
        # Use script with absolute paths for more reliable test
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            cmd = f"""
            echo 'test output' > {temp_path}
            cat {temp_path}
            """
            self.tester.assert_outputs_match(cmd)
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def test_append_redirection(self):
        """Test append redirection."""
        # Use script with absolute paths for more reliable test
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            cmd = f"""
            echo 'line 1' > {temp_path}
            echo 'line 2' >> {temp_path}
            cat {temp_path}
            """
            self.tester.assert_outputs_match(cmd)
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])