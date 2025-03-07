#!/usr/bin/env python3
"""
Framework for testing compatibility between psh and bash.

This module provides utilities to run the same commands through both
psh and bash shells and compare their outputs, exit codes, and side effects.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import difflib
import pytest
from typing import List, Dict, Tuple, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class CommandResult:
    """Result of executing a command in a shell."""
    stdout: str
    stderr: str
    exit_code: int
    
    def __eq__(self, other):
        if not isinstance(other, CommandResult):
            return False
        return (self.stdout == other.stdout and 
                self.stderr == other.stderr and 
                self.exit_code == other.exit_code)
    
    def __str__(self):
        return (f"Exit Code: {self.exit_code}\n"
                f"STDOUT:\n{self.stdout}\n"
                f"STDERR:\n{self.stderr}")


class ShellCompatibilityTester:
    """Utility for testing compatibility between psh and bash."""
    
    def __init__(self, psh_path: Optional[str] = None, bash_path: Optional[str] = None):
        """Initialize the tester with paths to shells.
        
        Args:
            psh_path: Path to the psh shell executable. If None, uses current package.
            bash_path: Path to the bash shell. If None, uses 'bash' from PATH.
        """
        # Find psh path if not provided
        if psh_path is None:
            # Use the installed psh module
            self.psh_path = [sys.executable, "-m", "src.shell"]
        else:
            self.psh_path = [psh_path]
        
        # Find bash path if not provided
        self.bash_path = [bash_path or "bash"]
    
    @contextmanager
    def _setup_test_environment(self) -> str:
        """Set up a clean test environment.
        
        Creates a temporary directory with controlled environment variables.
        
        Returns:
            Path to the temporary directory.
        """
        # Create a temporary directory for the test
        temp_dir = tempfile.mkdtemp(prefix="psh_compat_test_")
        old_cwd = os.getcwd()
        
        # Create basic profile files
        with open(os.path.join(temp_dir, ".bashrc"), "w") as f:
            f.write("# Empty bashrc\n")
        
        try:
            # Change to the temp directory
            os.chdir(temp_dir)
            yield temp_dir
        finally:
            # Clean up
            os.chdir(old_cwd)
            shutil.rmtree(temp_dir)
    
    def _run_shell_command(
        self, 
        shell_cmd: List[str], 
        input_text: str, 
        env: Optional[Dict[str, str]] = None
    ) -> CommandResult:
        """Run a command in the specified shell.
        
        Args:
            shell_cmd: The shell command to run (e.g. ["bash", "-c"])
            input_text: The input text to provide to the shell
            env: Environment variables to set
        
        Returns:
            CommandResult with stdout, stderr, and exit code
        """
        # Create a temporary script file for more reliable execution
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
            script_path = script_file.name
            # Use set -e to fail on error
            script_file.write("#!/bin/bash\n")
            script_file.write(input_text + "\n")
            
        # Make the script executable
        os.chmod(script_path, 0o755)
            
        try:
            # Set up base environment variables if not provided
            if env is None:
                env = os.environ.copy()
                
            # Disable shell history for consistency
            env["HISTFILE"] = "/dev/null"
            env["HISTSIZE"] = "0"
                
            # Run the shell process with the script
            process = subprocess.run(
                shell_cmd + [script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                universal_newlines=True
            )
            
            return CommandResult(
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode
            )
        finally:
            # Clean up the temporary script
            try:
                os.unlink(script_path)
            except:
                pass
    
    def run_in_psh(self, command: str, env: Optional[Dict[str, str]] = None) -> CommandResult:
        """Run a command in psh.
        
        Args:
            command: The command to run
            env: Optional environment variables
            
        Returns:
            CommandResult with stdout, stderr, and exit code
        """
        return self._run_shell_command(self.psh_path + ["-c"], command, env)
    
    def run_in_bash(self, command: str, env: Optional[Dict[str, str]] = None) -> CommandResult:
        """Run a command in bash.
        
        Args:
            command: The command to run
            env: Optional environment variables
            
        Returns:
            CommandResult with stdout, stderr, and exit code
        """
        return self._run_shell_command(self.bash_path + ["-c"], command, env)
    
    def compare_outputs(
        self, 
        command: str, 
        env: Optional[Dict[str, str]] = None,
        ignore_exit_code: bool = False,
        ignore_stderr: bool = False,
        normalize_whitespace: bool = True,
        ignore_empty_lines: bool = True
    ) -> Tuple[bool, CommandResult, CommandResult, str]:
        """Compare output of running the same command in psh and bash.
        
        Args:
            command: The command to run in both shells
            env: Optional environment variables
            ignore_exit_code: Whether to ignore differences in exit codes
            ignore_stderr: Whether to ignore differences in stderr
            normalize_whitespace: Whether to normalize whitespace
            ignore_empty_lines: Whether to ignore empty lines
            
        Returns:
            Tuple of (match, psh_result, bash_result, diff)
        """
        # Run in both shells
        psh_result = self.run_in_psh(command, env)
        bash_result = self.run_in_bash(command, env)
        
        # Process outputs if requested
        if normalize_whitespace:
            psh_result.stdout = self._normalize_whitespace(psh_result.stdout)
            bash_result.stdout = self._normalize_whitespace(bash_result.stdout)
            if not ignore_stderr:
                psh_result.stderr = self._normalize_whitespace(psh_result.stderr)
                bash_result.stderr = self._normalize_whitespace(bash_result.stderr)
        
        if ignore_empty_lines:
            psh_result.stdout = self._remove_empty_lines(psh_result.stdout)
            bash_result.stdout = self._remove_empty_lines(bash_result.stdout)
            if not ignore_stderr:
                psh_result.stderr = self._remove_empty_lines(psh_result.stderr)
                bash_result.stderr = self._remove_empty_lines(bash_result.stderr)
        
        # Generate diff
        stdout_diff = self._generate_diff(
            bash_result.stdout.splitlines(), 
            psh_result.stdout.splitlines(),
            "bash stdout",
            "psh stdout"
        )
        
        stderr_diff = ""
        if not ignore_stderr:
            stderr_diff = self._generate_diff(
                bash_result.stderr.splitlines(), 
                psh_result.stderr.splitlines(),
                "bash stderr",
                "psh stderr"
            )
        
        # Check if outputs match
        match = True
        if psh_result.stdout != bash_result.stdout:
            match = False
        if not ignore_stderr and psh_result.stderr != bash_result.stderr:
            match = False
        if not ignore_exit_code and psh_result.exit_code != bash_result.exit_code:
            match = False
        
        diff = f"{stdout_diff}\n{stderr_diff}" if stderr_diff else stdout_diff
        if not ignore_exit_code and psh_result.exit_code != bash_result.exit_code:
            diff += f"\nExit codes differ: bash={bash_result.exit_code}, psh={psh_result.exit_code}"
            
        return match, psh_result, bash_result, diff.strip()
    
    def assert_outputs_match(
        self, 
        command: str, 
        env: Optional[Dict[str, str]] = None,
        ignore_exit_code: bool = False,
        ignore_stderr: bool = False,
        normalize_whitespace: bool = True,
        ignore_empty_lines: bool = True
    ) -> None:
        """Assert that psh and bash output match for a given command.
        
        Args:
            command: The command to run in both shells
            env: Optional environment variables
            ignore_exit_code: Whether to ignore differences in exit codes
            ignore_stderr: Whether to ignore differences in stderr
            normalize_whitespace: Whether to normalize whitespace
            ignore_empty_lines: Whether to ignore empty lines
            
        Raises:
            AssertionError: If the outputs do not match
        """
        match, psh_result, bash_result, diff = self.compare_outputs(
            command,
            env=env,
            ignore_exit_code=ignore_exit_code,
            ignore_stderr=ignore_stderr,
            normalize_whitespace=normalize_whitespace,
            ignore_empty_lines=ignore_empty_lines
        )
        
        if not match:
            error_msg = f"Command '{command}' produced different outputs in psh and bash:\n{diff}"
            pytest.fail(error_msg)
    
    @contextmanager
    def compatibility_test(self, commands: List[str], setup_commands: Optional[List[str]] = None) -> None:
        """Run a compatibility test with a sequence of commands.
        
        Creates a test environment, runs setup commands, then tests each command.
        
        Args:
            commands: List of commands to test
            setup_commands: List of commands to run before testing (not compared)
            
        Yields:
            Nothing. Use this as a context manager.
        """
        with self._setup_test_environment() as temp_dir:
            # Run setup commands if any
            if setup_commands:
                for cmd in setup_commands:
                    # Run setup commands in bash only
                    self.run_in_bash(cmd)
                    
            # Test each command
            try:
                yield
                
                for cmd in commands:
                    self.assert_outputs_match(cmd)
            except Exception as e:
                pytest.fail(f"Compatibility test failed: {str(e)}")
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with a single space
        import re
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace
        return text.strip()
    
    def _remove_empty_lines(self, text: str) -> str:
        """Remove empty lines from text.
        
        Args:
            text: Input text
            
        Returns:
            Text without empty lines
        """
        return "\n".join(line for line in text.splitlines() if line.strip())
    
    def _generate_diff(
        self, 
        expected_lines: List[str], 
        actual_lines: List[str],
        expected_name: str = "expected",
        actual_name: str = "actual"
    ) -> str:
        """Generate a diff between expected and actual output.
        
        Args:
            expected_lines: Expected output lines
            actual_lines: Actual output lines
            expected_name: Label for expected output
            actual_name: Label for actual output
            
        Returns:
            Diff as a string
        """
        diff = difflib.unified_diff(
            expected_lines,
            actual_lines,
            fromfile=expected_name,
            tofile=actual_name,
            lineterm=""
        )
        return "\n".join(diff)


# Helper functions to create individual compatibility tests

def create_compatibility_test(command: str, **kwargs) -> callable:
    """Create a test function that checks compatibility for a single command.
    
    Args:
        command: The command to test
        **kwargs: Additional arguments for assert_outputs_match
        
    Returns:
        A test function
    """
    def test_func():
        tester = ShellCompatibilityTester()
        tester.assert_outputs_match(command, **kwargs)
    return test_func


def create_multi_command_test(
    commands: List[str], 
    setup_commands: Optional[List[str]] = None, 
    **kwargs
) -> callable:
    """Create a test function that runs multiple commands, checking compatibility.
    
    Args:
        commands: List of commands to test
        setup_commands: Commands to run before testing
        **kwargs: Additional arguments for assert_outputs_match
        
    Returns:
        A test function
    """
    def test_func():
        tester = ShellCompatibilityTester()
        with tester.compatibility_test(commands, setup_commands):
            pass
    return test_func


# Examples of using the framework
if __name__ == "__main__":
    # Example usage
    tester = ShellCompatibilityTester()
    
    # Test a simple command
    match, psh_result, bash_result, diff = tester.compare_outputs("echo 'Hello, World!'")
    print(f"Match: {match}")
    print(diff if not match else "Outputs match!")
    
    # Test a more complex command
    result = tester.compare_outputs("for i in 1 2 3; do echo $i; done")
    print(f"Match: {result[0]}")
    print(result[3] if not result[0] else "Outputs match!")