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

def version() -> int:
    """Display shell version information
    
    Returns:
        int: Always returns 0 (success)
    """
    try:
        from .. import __version__
        print(f"Python Shell version {__version__}")
    except (ImportError, AttributeError):
        print("Python Shell version 0.1.0")
    print(f"Python {sys.version}")
    return 0

def source(filename: Optional[str] = None) -> int:
    """Execute commands from a file in the current shell context
    
    Usage:
        source filename    # Execute commands from filename
        . filename        # Alternative syntax
        
    Returns:
        Exit status of the last command executed, or 1 if an error occurs
    """
    if filename is None:
        sys.stderr.write("source: filename argument required\n")
        return 1
    
    try:
        # Get full path to script
        filepath = os.path.expanduser(filename)
        
        # Read the file content
        with open(filepath) as f:
            script_content = f.read().strip()
        
        # We'll use a direct approach
        # Execute each line directly one at a time in the current context
        
        # Split into lines and execute each separately
        lines = script_content.splitlines()
        exit_status = 0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                # Handle variable assignments directly
                if "=" in line and not any(cmd in line for cmd in ["export", "echo", "if", "for", "while"]):
                    var_name, var_value = line.split("=", 1)
                    os.environ[var_name] = var_value
                    continue
                    
                # Parse export command manually for simpler cases
                if line.startswith("export ") and "=" in line:
                    # Extract the variable portion after export
                    var_part = line[7:].strip()
                    var_name, var_value = var_part.split("=", 1)
                    os.environ[var_name] = var_value
                    continue
                    
                # For other commands, use shell execution
                from ..shell import Shell
                result = Shell(debug_mode=False).execute_line(line)
                if result is not None:
                    exit_status = result
                    
            except Exception as e:
                sys.stderr.write(f"source: error executing '{line}': {e}\n")
                exit_status = 1
        
        return exit_status
            
    except FileNotFoundError:
        sys.stderr.write(f"source: {filename}: No such file\n")
        return 1
    except PermissionError:
        sys.stderr.write(f"source: {filename}: Permission denied\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"source: error reading {filename}: {e}\n")
        return 1


def function_command(name: str = None, *args) -> int:
    """Define a shell function.
    
    This is only used as a fallback for when the parser doesn't recognize
    a function definition correctly.
    
    Usage:
        function name() { commands; }
    
    Returns:
        0 on success, 1 on error
    """
    from ..context import SHELL
    
    # Need at least a name
    if not name:
        print("function: missing function name", file=sys.stderr)
        return 1
    
    # Get the current shell instance
    shell_instance = SHELL.get_current_shell()
    if not shell_instance:
        print("function: no active shell instance", file=sys.stderr)
        return 1
    
    # Use the shell to execute the function definition properly
    try:
        # Build the function definition
        function_def = f"function {name}"
        if args:
            function_def += "() { " + "; ".join(args) + "; }"
        else:
            function_def += "() { :; }" # Empty function
        
        # Execute the function definition
        shell_instance.execute_line(function_def)
        return 0
    except Exception as e:
        print(f"function: error defining function {name}: {e}", file=sys.stderr)
        return 1


def prompt(template: Optional[str] = None, *_args) -> int:
    """Change or display the shell prompt template.
    
    Usage:
        prompt                 - Display current prompt template
        prompt "new_template"  - Set prompt to the given template
        prompt -h              - Show help with available prompt variables
        prompt -l              - List predefined prompt templates
        
    Returns:
        0 on success, 1 on error
    """
    from ..context import SHELL
    from ..config.manager import ConfigManager
    from ..utils.prompt import PromptFormatter
    
    # Get the current shell instance
    shell_instance = SHELL.get_current_shell()
    if not shell_instance:
        sys.stderr.write("prompt: no active shell instance\n")
        return 1
    
    # Get the config manager
    if hasattr(SHELL, '_config_manager'):
        config_manager = SHELL._config_manager
    elif hasattr(shell_instance, 'config_manager'):
        config_manager = shell_instance.config_manager
    else:
        config_manager = ConfigManager()
    
    # Display help info
    if template in ("-h", "--help"):
        print("Prompt Variables:")
        print("  \\u - Username")
        print("  \\h - Hostname (short)")
        print("  \\H - Hostname (FQDN)")
        print("  \\w - Current working directory")
        print("  \\W - Basename of current directory")
        print("  \\$ - # for root, $ for regular user")
        print("  \\? - Exit status (colored)")
        print("  \\e - Raw exit status")
        print("  \\t - Current time (HH:MM:SS)")
        print("  \\T - Current time (12-hour)")
        print("  \\d - Current date")
        print("  \\g - Git branch")
        print("  \\j - Number of jobs")
        print("  \\! - History number")
        print("  \\v - Python virtualenv")
        print("\nColor codes:")
        print("  \\[COLOR] - Start color (e.g. \\[red])")
        print("  \\[reset] - Reset color")
        print("\nAvailable colors:")
        for color in sorted(PromptFormatter.COLORS.keys()):
            print(f"  {color}")
        return 0
    
    # List predefined prompts
    if template in ("-l", "--list"):
        print("Predefined prompts:")
        print("  default    - \\[blue]\\u@\\h\\[reset]:\\[cyan]\\w\\[reset] \\[green]\\g\\[reset]\\$ ")
        print("  minimal    - \\$ ")
        print("  basic      - \\u@\\h:\\w\\$ ")
        print("  path       - \\w\\$ ")
        print("  full       - [\\t] \\u@\\h:\\w \\g (\\j) \\$ ")
        print("  git        - \\w \\[green]\\g\\[reset]\\$ ")
        print("  status     - [\\?] \\w\\$ ")
        return 0
    
    # With no arguments, display current template
    if template is None:
        current = config_manager.get('prompt_template')
        print(f"Current prompt template: {current}")
        return 0
    
    # Handle predefined prompts
    predefined = {
        "default": "\\[blue]\\u@\\h\\[reset]:\\[cyan]\\w\\[reset] \\[green]\\g\\[reset]\\$ ",
        "minimal": "\\$ ",
        "basic": "\\u@\\h:\\w\\$ ",
        "path": "\\w\\$ ",
        "full": "[\\t] \\u@\\h:\\w \\g (\\j) \\$ ",
        "git": "\\w \\[green]\\g\\[reset]\\$ ",
        "status": "[\\?] \\w\\$ "
    }
    
    # Use predefined template if specified
    if template in predefined:
        actual_template = predefined[template]
    else:
        # When used from command line, backslashes are literal rather than escape characters
        # We need to add backslashes to each prompt variable character
        prompt_vars = 'uhHwW$?etTdgj!v'
        if all(f'\\{var}' not in template for var in prompt_vars):
            # None of the properly escaped variables are present, assume we need to add backslashes
            actual_template = ""
            i = 0
            while i < len(template):
                if i < len(template) - 1 and template[i] == '\\':
                    # Skip escape sequences
                    actual_template += template[i:i+2]
                    i += 2
                elif template[i] in prompt_vars:
                    # Add backslash before prompt variable characters
                    actual_template += f'\\{template[i]}'
                    i += 1
                else:
                    # Regular character, pass through unchanged
                    actual_template += template[i]
                    i += 1
        else:
            # Template already has proper escapes, use as is
            actual_template = template
    
    # Set new prompt template and test it
    try:
        config_manager.set('prompt_template', actual_template)
        # Test the new template
        formatter = PromptFormatter()
        formatted = formatter.format(actual_template)
        print(f"Prompt set to: {formatted}")
        return 0
    except Exception as e:
        sys.stderr.write(f"prompt: error setting prompt: {e}\n")
        return 1