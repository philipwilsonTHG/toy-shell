#!/usr/bin/env python3
"""
Handling of special shell variables like $$, $?, $@, etc.
"""

import os
import sys
import signal
from typing import List, Dict, Any, Optional, Callable

from ..context import SHELL


class SpecialVariableHandler:
    """Handles special shell variables like $$, $?, $@, etc."""
    
    def __init__(self):
        """Initialize the special variable handler."""
        # Store positional parameters (arguments)
        self._positional_params: List[str] = []
        
        # Last background process ID
        self._last_bg_pid: Optional[int] = None
        
        # Current shell options
        self._shell_options: str = "h"  # Default interactive shell options
        
        # Script/command name
        self._script_name: str = "psh"
        
    def set_positional_params(self, params: List[str]) -> None:
        """Set the positional parameters ($1, $2, etc.).
        
        Args:
            params: List of parameter values
        """
        self._positional_params = params.copy()
        
    def get_positional_param(self, index: int) -> str:
        """Get a positional parameter value.
        
        Args:
            index: Parameter index (1-based)
            
        Returns:
            Parameter value or empty string if not set
        """
        if index <= 0 or index > len(self._positional_params):
            return ""
        return self._positional_params[index - 1]
    
    def set_last_bg_pid(self, pid: int) -> None:
        """Set the last background process ID ($!).
        
        Args:
            pid: Process ID of the last background process
        """
        self._last_bg_pid = pid
        
    def get_last_bg_pid(self) -> str:
        """Get the last background process ID ($!).
        
        Returns:
            PID as string, or empty string if no background process
        """
        return str(self._last_bg_pid) if self._last_bg_pid is not None else ""
    
    def set_script_name(self, name: str) -> None:
        """Set the script or shell name ($0).
        
        Args:
            name: Script or shell name
        """
        self._script_name = name
        
    def get_script_name(self) -> str:
        """Get the script or shell name ($0).
        
        Returns:
            Script or shell name
        """
        return self._script_name
    
    def set_shell_options(self, options: str) -> None:
        """Set the shell option flags ($-).
        
        Args:
            options: Shell option flags as a string
        """
        self._shell_options = options
        
    def get_shell_options(self) -> str:
        """Get the shell option flags ($-).
        
        Returns:
            Shell option flags as a string
        """
        return self._shell_options
    
    def get_special_variable(self, name: str) -> str:
        """Get the value of a special variable.
        
        Args:
            name: Variable name without $ prefix
            
        Returns:
            Variable value or None if not a special variable
        """
        # Remove the $ from the name if it was included
        if name.startswith('$'):
            name = name[1:]
            
        # Process ID of current shell
        if name == "$":
            return str(os.getpid())
        
        # Exit status of last command
        elif name == "?":
            # Get last exit status from shell or environment
            shell = SHELL.get_current_shell()
            if shell and hasattr(shell, 'last_exit_status'):
                return str(shell.last_exit_status)
            return "0"  # Default exit status
        
        # PID of last background command
        elif name == "!":
            return self.get_last_bg_pid()
        
        # Shell option flags
        elif name == "-":
            return self.get_shell_options()
        
        # Script/command name
        elif name == "0":
            return self.get_script_name()
        
        # Number of positional parameters
        elif name == "#":
            return str(len(self._positional_params))
        
        # All positional parameters as a single string
        elif name == "*":
            return " ".join(self._positional_params)
        
        # All positional parameters as separate strings
        elif name == "@":
            return " ".join(self._positional_params)
        
        # Positional parameters
        elif name.isdigit():
            index = int(name)
            return self.get_positional_param(index)
        
        # Not a special variable
        return None
    
    def expand_special_variables(self, text: str) -> str:
        """Expand special variables in a string.
        
        Args:
            text: Text containing special variables
            
        Returns:
            Text with special variables expanded
        """
        # This is a simple implementation that only handles basic cases
        # For a complete implementation, use the state machine expander
        result = text
        
        # Replace $$ with process ID
        if "$$" in result:
            result = result.replace("$$", self.get_special_variable("$"))
        
        # Replace $? with exit status
        if "$?" in result:
            result = result.replace("$?", self.get_special_variable("?"))
        
        # Replace $! with last background PID
        if "$!" in result:
            result = result.replace("$!", self.get_special_variable("!"))
        
        # Replace $- with shell options
        if "$-" in result:
            result = result.replace("$-", self.get_special_variable("-"))
        
        # Replace $0 with script name
        if "$0" in result:
            result = result.replace("$0", self.get_special_variable("0"))
        
        # Replace $# with argument count
        if "$#" in result:
            result = result.replace("$#", self.get_special_variable("#"))
        
        # Replace $* with all args
        if "$*" in result:
            result = result.replace("$*", self.get_special_variable("*"))
        
        # Replace $@ with all args
        if "$@" in result:
            result = result.replace("$@", self.get_special_variable("@"))
        
        # Replace positional parameters
        for i in range(1, 10):  # Handle $1 through $9
            var = f"${i}"
            if var in result:
                result = result.replace(var, self.get_special_variable(str(i)))
        
        return result


# Create a global instance for the shell to use
SPECIAL_VARS = SpecialVariableHandler()

def register_special_variable_handler(scope_provider: Callable[[str], Optional[str]]) -> Callable[[str], Optional[str]]:
    """Register the special variable handler with the scope provider.
    
    Args:
        scope_provider: Function that provides variable values from the current scope
        
    Returns:
        An enhanced scope provider that handles special variables
    """
    # The scope provider is a function that looks up variable values
    # We need to modify it to check for special variables first
    
    original_provider = scope_provider
    
    def enhanced_scope_provider(name: str) -> Optional[str]:
        # Special handling for variable names that need explicit mapping
        if name == "$":
            return str(os.getpid())
        elif name == "0":
            return SPECIAL_VARS.get_script_name()
        
        # Check for special variables with standard handling
        special_value = SPECIAL_VARS.get_special_variable(name)
        if special_value is not None:
            return special_value
        
        # Fall back to the original scope provider
        return original_provider(name)
    
    # Return the enhanced provider
    return enhanced_scope_provider