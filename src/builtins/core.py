#!/usr/bin/env python3

import os
import sys
from typing import Optional
from ..context import SHELL

def cd(newdir: Optional[str] = None) -> None:
    """Change current working directory"""
    # Default to home directory if no argument
    newdir = os.path.expanduser("~") if newdir is None else newdir
    
    # Handle cd - to go to previous directory
    if newdir == "-":
        # Check if OLDPWD environment variable exists
        if "OLDPWD" in os.environ:
            newdir = os.environ["OLDPWD"]
            print(newdir)  # Print the directory we're changing to, like bash does
        # Fallback to history if OLDPWD not set but we have history
        elif len(SHELL.cwd_history) >= 2:
            newdir = SHELL.cwd_history[-2]
            print(newdir)  # Print the directory we're changing to
        else:
            newdir = '.'
            # sys.stderr.write("cd: OLDPWD not set\n")
            # return
    
    try:
        # Save current directory before changing
        olddir = os.getcwd()
        os.chdir(os.path.expanduser(newdir))
        
        # Set OLDPWD environment variable to the previous directory
        os.environ["OLDPWD"] = olddir
        
        # Also maintain our history for fallback
        SHELL.cwd_history.append(os.getcwd())  # Add the new directory, not olddir
        
        # Keep history at reasonable size
        if len(SHELL.cwd_history) > 20:
            SHELL.cwd_history.pop(0)

        return True
            
    except Exception as e:
        sys.stderr.write(f"cd: {newdir}: {e.strerror}\n")

def exit_shell(status_code: str = "0") -> int:
    """Exit the shell with optional status code
    
    Returns a special code to indicate shell should exit rather than calling sys.exit
    """
    try:
        # Parse status code, default to 0 if not numeric
        code = int(status_code) if status_code.isnumeric() else 0
        # Ensure status code is in valid range (0-255)
        code = code & 0xFF
        # Return -1000 - code as special marker for shell to exit
        # We use -1000 - code instead of -1000 + code to ensure all values are negative
        return -1000 - code
    except ValueError:
        sys.stderr.write(f"exit: invalid status code: {status_code}\n")
        return -1001  # Special error exit code

def version() -> None:
    """Display shell version information"""
    try:
        from .. import __version__
        print(f"Python Shell version {__version__}")
    except (ImportError, AttributeError):
        print("Python Shell version 0.1.0")
    print(f"Python {sys.version}")

def source(filename: Optional[str] = None) -> None:
    """Execute commands from a file"""
    if filename is None:
        sys.stderr.write("source: filename argument required\n")
        return
    
    try:
        filepath = os.path.expanduser(filename)
        with open(filepath) as f:
            from ..shell import process_line
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    try:
                        process_line(line)
                    except Exception as e:
                        sys.stderr.write(f"source: error executing '{line}': {e}\n")
                        return
    except FileNotFoundError:
        sys.stderr.write(f"source: {filename}: No such file\n")
    except PermissionError:
        sys.stderr.write(f"source: {filename}: Permission denied\n")
    except Exception as e:
        sys.stderr.write(f"source: error reading {filename}: {e}\n")
