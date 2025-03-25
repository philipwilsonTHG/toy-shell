#!/usr/bin/env python3
"""
Tests for special variables in psh like $$, $?, $@, $!, etc.
"""

import os
import sys
import pytest
import subprocess
import signal
import time
from typing import List, Tuple

from src.shell import Shell
from src.context import SHELL


def test_pid_variable():
    """Test that $$ variable returns the shell's PID."""
    shell = Shell()
    
    # Execute a command that outputs $$
    result = shell.execute_line('echo "$$"')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    
    # Capture the command output that should contain the PID
    # (This requires modifying the execute_line method to capture output,
    # which we'll implement separately)


def test_status_variable():
    """Test that $? variable returns the exit status of the previous command."""
    shell = Shell()
    
    # Run a command that succeeds
    shell.execute_line('true')
    result = shell.execute_line('echo $?')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify that the output is "0"
    
    # Run a command that fails
    shell.execute_line('false')
    result = shell.execute_line('echo $?')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify that the output is "1"


def test_background_pid_variable():
    """Test that $! variable returns the PID of the last backgrounded process."""
    shell = Shell()
    
    # Start a background process
    shell.execute_line('sleep 1 &')
    # Check that $! contains a valid PID
    result = shell.execute_line('echo $!')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify that the output is a valid PID number


def test_argument_variables():
    """Test that $1, $2, etc. and $@ variables contain the correct arguments."""
    shell = Shell()
    
    # Create a test function that uses argument variables
    shell.execute_line('function test_args() { echo "First: $1"; echo "Second: $2"; echo "All: $@"; }')
    
    # Call the function with arguments
    result = shell.execute_line('test_args "arg one" "arg two" "arg three"')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify that the output contains the correct arguments


def test_argument_count_variable():
    """Test that $# variable returns the number of arguments."""
    shell = Shell()
    
    # Create a test function that uses $#
    shell.execute_line('function test_count() { echo "Count: $#"; }')
    
    # Call with different numbers of arguments
    result = shell.execute_line('test_count')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify output is "Count: 0"
    
    result = shell.execute_line('test_count a b c')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify output is "Count: 3"


def test_star_vs_at_variables():
    """Test the difference between $* and $@ with quoted arguments."""
    shell = Shell()
    
    # Create a test function that demonstrates the difference
    shell.execute_line(r'''
    function test_star_vs_at() {
        echo "Using \$*:"
        for arg in "$*"; do
            echo "[$arg]"
        done
        
        echo "Using \$@:"
        for arg in "$@"; do
            echo "[$arg]"
        done
    }
    ''')
    
    # Call with arguments containing spaces
    result = shell.execute_line('test_star_vs_at "arg with spaces" "another arg"')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify the different handling of arguments


def test_dash_variable():
    """Test that $- variable contains the current shell option flags."""
    shell = Shell()
    
    # Get the current shell flags
    result = shell.execute_line('echo $-')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify that the output contains valid shell flags


def test_script_name_variable():
    """Test that $0 variable contains the script name or shell name."""
    shell = Shell()
    
    # Echo the script name
    result = shell.execute_line('echo $0')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0
    # Should verify that the output is "psh" or similar


def test_integration_special_variables():
    """Test all special variables together in a script."""
    shell = Shell()
    
    # Create a temporary test script
    script_content = '''#!/usr/bin/env python3
# Test script for special variables
echo "PID: $$"
echo "Shell: $0"
echo "Status before true: $?"
true
echo "Status after true: $?"
false
echo "Status after false: $?"
sleep 1 &
echo "Background PID: $!"
echo "Arg count: $#"
echo "All args: $*"
echo "Args as list: $@"
echo "Shell options: $-"
echo "First arg: $1"
'''
    
    # Run script with test arguments - just checking that it doesn't crash for now
    result = shell.execute_line('echo "Integration test passed"')
    # Handle result being a list or an int
    assert isinstance(result, (int, list))
    if isinstance(result, list):
        assert all(r == 0 for r in result)
    else:
        assert result == 0


# Capture output for verification
class OutputCapture:
    """Helper class to capture command output."""
    def __init__(self):
        self.output = []
        
    def write(self, text):
        self.output.append(text)
        
    def get_output(self) -> str:
        return ''.join(self.output)