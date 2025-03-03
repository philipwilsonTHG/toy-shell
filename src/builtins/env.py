#!/usr/bin/env python3

import os
import sys
from typing import Optional, List

def export(*args: str) -> None:
    """Set or display environment variables
    
    Usage:
        export           # Display all environment variables
        export VAR=val  # Set environment variable
        export VAR=""   # Set to empty string
    """
    if not args:
        # Print all environment variables when no args provided
        for key, value in sorted(os.environ.items()):
            print(f"{key}={value}")
        return True

    for arg in args:
        if '=' in arg:
            # Setting a variable
            try:
                key, value = arg.split("=", 1)
                if not key or not key.isidentifier():
                    sys.stderr.write(f"export: invalid format: {arg}\n")
                    continue
                # Handle quoted values
                value = value.strip("\"'")
                os.environ[key] = value
            except ValueError:
                sys.stderr.write(f"export: invalid format: {arg}\n")
        else:
            # Showing variable value
            if arg in os.environ:
                print(f"{arg}={os.environ[arg]}")
            else:
                sys.stderr.write(f"export: {arg}: not found\n")
    return True

def unset(*args: str) -> None:
    """Remove environment variables
    
    Usage:
        unset VAR [VAR ...]  # Remove one or more environment variables
    """
    if not args:
        sys.stderr.write("unset: missing variable name\n")
        return
    
    for arg in args:
        try:
            # Validate variable name
            if not arg.isidentifier():
                sys.stderr.write(f"unset: invalid variable name: {arg}\n")
                continue
            
            del os.environ[arg]
        except KeyError:
            sys.stderr.write(f"unset: {arg}: not found\n")
