#!/usr/bin/env python3
"""
Shell compatibility tests using the compatibility testing framework.

This file demonstrates how to use the compatibility framework to create
tests that compare psh behavior with bash.
"""

import os
import tempfile
import pytest
from tests.compatibility import (
    ShellCompatibilityTester,
    create_compatibility_test,
    create_multi_command_test
)


# Basic test with direct API
def test_simple_command():
    """Test a simple command."""
    tester = ShellCompatibilityTester()
    tester.assert_outputs_match("echo 'Hello, World!'")


# Test using factory function - simple test
test_echo_with_factory = create_compatibility_test("echo 'Created with factory'")

# Example of a multi-command test using the factory approach
def create_factory_multi_command_test():
    # Create a test file path using a predictable location
    test_file = os.path.join(tempfile.gettempdir(), "factory_test.txt")
    
    # Create commands using absolute path
    commands = [
        f"echo 'Line 1' > {test_file}",
        f"echo 'Line 2' >> {test_file}",
        f"cat {test_file}"
    ]
    
    # Setup and cleanup commands
    setup = [f"rm -f {test_file}"]  # Make sure file doesn't exist at start
    
    # Create and return test function
    test_func = create_multi_command_test(
        commands=commands,
        setup_commands=setup
    )
    
    return test_func

# Create the test
test_factory_multi = create_factory_multi_command_test()


# Multi-command test using a temporary file
def test_multi_command():
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Run sequence of commands on a temp file
        commands = [
            f"echo 'Step 1' > {temp_path}",
            f"echo 'Step 2' >> {temp_path}",
            f"cat {temp_path}"
        ]
        
        tester = ShellCompatibilityTester()
        for cmd in commands:
            tester.assert_outputs_match(cmd)
    finally:
        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass


# Parameterized test
@pytest.mark.parametrize("command", [
    "echo 'Test 1'",
    "echo 'Test 2' | wc -w",
    "echo $HOME | grep /",
])
def test_parameterized_commands(command):
    """Test various commands through parameterization."""
    tester = ShellCompatibilityTester()
    tester.assert_outputs_match(command)


# Class-based tests
class TestShellFeatures:
    """Demonstrate class-based testing approach."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_variable_expansion(self):
        """Test variable expansion."""
        self.tester.assert_outputs_match("x='value'; echo $x")
    
    def test_command_substitution(self):
        """Test command substitution."""
        self.tester.assert_outputs_match("echo $(echo substitution)")
    
    @pytest.mark.parametrize("command,expected_exit", [
        ("true", 0),
        ("false", 1),
        ("ls /nonexistent", 1),
    ])
    def test_exit_codes(self, command, expected_exit):
        """Test exit code handling."""
        result = self.tester.run_in_psh(command)
        assert result.exit_code == expected_exit
        
        # Can also compare with bash directly
        bash_result = self.tester.run_in_bash(command)
        assert result.exit_code == bash_result.exit_code


# Run these tests directly with pytest
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])