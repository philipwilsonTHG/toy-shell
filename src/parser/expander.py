#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import tempfile
from typing import Optional, Match
from .quotes import is_quoted, strip_quotes, handle_quotes

def expand_variables(text: str) -> str:
    """Expand environment variables in text"""
    def replace_var(match: Match[str]) -> str:
        var = match.group(1)
        if not var:
            return match.group(0)
        
        # Handle ${VAR} format
        if match.group(0).startswith('${'):
            # No modifier case - direct variable lookup
            if ':' not in var:
                return os.environ.get(var, '')
                
            # Handle modifiers
            var, modifier = var.split(':', 1)
            value = os.environ.get(var, '')
            
            # Handle :N:M substring (bash substring extraction)
            if re.match(r'^\d+:\d*$', modifier):
                try:
                    parts = modifier.split(':')
                    start = int(parts[0])
                    if len(parts) > 1 and parts[1]:
                        length = int(parts[1])
                        return value[start:start + length]
                    else:
                        return value[start:]
                except (ValueError, IndexError):
                    return ''
            
            # Handle :- := :? :+ operators
            if modifier.startswith('-'):
                return modifier[1:] if not value else value
            elif modifier.startswith('='):
                if not value:
                    os.environ[var] = modifier[1:]
                    return modifier[1:]
                return value
            elif modifier.startswith('?'):
                if not value:
                    raise ValueError(f"{var}: {modifier[1:]}")
                return value
            elif modifier.startswith('+'):
                return modifier[1:] if value else ''
            
            return value
        
        # Handle $VAR format - standard variable substitution
        # Variable names must be exactly matched, not split at underscores (standard bash behavior)
        return os.environ.get(var, '')
    
    # Handle ${VAR} and ${VAR:modifier}
    text = re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    # Handle $VAR
    text = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', replace_var, text)
    
    return text

def expand_arithmetic(text: str) -> str:
    """Expand $(( expression )) arithmetic expansions using Python's eval()"""
    
    # Handle $(( expression )) format
    if text.startswith('$((') and text.endswith('))'):
        expression = text[3:-2].strip()
    else:
        return text
    
    if not expression:
        return '0'  # Empty expressions evaluate to 0 in POSIX shells
    
    # First, handle nested arithmetic expressions like $((1 + $((2 * 3))))
    nested_pattern = r'\$\(\(([^()]*(?:\([^()]*\)[^()]*)*)\)\)'
    while re.search(nested_pattern, expression):
        def replace_nested(match):
            inner_expr = match.group(0)
            inner_result = expand_arithmetic(inner_expr)
            return inner_result
        
        expression = re.sub(nested_pattern, replace_nested, expression)
    
    # Replace shell variables with their values
    var_pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)'
    def replace_var(match):
        var_name = match.group(1)
        # Get value from environment, default to 0 if not found
        value = os.environ.get(var_name, '0')
        # Ensure the value is a number, default to 0 if not
        try:
            float(value)  # Just to check if it's a valid number
            return value
        except ValueError:
            return '0'
        
    expression = re.sub(var_pattern, replace_var, expression)
    
    # Convert shell-style operators to Python equivalents
    expression = expression.replace('&&', ' and ')
    expression = expression.replace('||', ' or ')
    expression = expression.replace('!', ' not ')
    
    # Handle ternary operator: a ? b : c -> b if a else c
    ternary_pattern = r'([^?]+)\?([^:]+):(.+)'
    ternary_match = re.search(ternary_pattern, expression)
    if ternary_match:
        cond = ternary_match.group(1).strip()
        true_val = ternary_match.group(2).strip()
        false_val = ternary_match.group(3).strip()
        expression = f"({true_val} if {cond} else {false_val})"
    
    # Evaluate using Python's eval() with a restricted namespace
    try:
        # Create a safe subset of allowed functions/operators
        safe_dict = {
            'abs': abs, 'int': int, 'float': float,
            'min': min, 'max': max, 'round': round
        }
        
        # Set a timeout to prevent infinite loops
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Evaluation timed out")
        
        # Set 1-second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(1)
        
        # Create a namespace where undefined variables evaluate to 0 (POSIX behavior)
        class PosixNamespace(dict):
            def __missing__(self, key):
                return 0
        
        namespace = PosixNamespace()
        namespace.update(safe_dict)
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, namespace)
        
        # Cancel the alarm
        signal.alarm(0)
        
        # Convert to integer if it's a float with no decimal part
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        # Convert booleans to integers (True->1, False->0)
        elif isinstance(result, bool):
            result = 1 if result else 0
        
        return str(result)
    except Exception as e:
        print(f"Error in arithmetic expansion: {e}", file=sys.stderr)
        return "0"  # Default to 0 on errors, like bash does

def expand_command_substitution(text: str) -> str:
    """Expand $(command) and `command` substitutions in text"""
    
    # Handle $(command) format
    if text.startswith('$(') and text.endswith(')'):
        command = text[2:-1].strip()
    # Handle `command` format
    elif text.startswith('`') and text.endswith('`'):
        command = text[1:-1].strip()
    else:
        return text
    
    if not command:
        return ''
    
    # Recursively handle nested command substitutions
    nested_pattern = r'\$\(([^()]*(?:\([^()]*\)[^()]*)*)\)'
    while re.search(nested_pattern, command):
        def replace_nested(match):
            inner_cmd = match.group(0)
            inner_result = expand_command_substitution(inner_cmd)
            return inner_result
        
        command = re.sub(nested_pattern, replace_nested, command)
    
    # Also handle nested backticks
    nested_backtick_pattern = r'`([^`]*(?:\\`[^`]*)*)`'
    while re.search(nested_backtick_pattern, command):
        def replace_nested_backtick(match):
            inner_cmd = match.group(0)
            inner_result = expand_command_substitution(inner_cmd)
            return inner_result
        
        command = re.sub(nested_backtick_pattern, replace_nested_backtick, command)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.stdout.strip() if result.returncode == 0 else ''
    except subprocess.SubprocessError:
        return ''

def expand_tilde(text: str) -> str:
    """Expand tilde (~) in paths"""
    if text == '~' or text.startswith('~/'):
        return os.path.expanduser(text)
    
    # ~user/path
    match = re.match(r'^~([^/]*)(/.*)?$', text)
    if match:
        user = match.group(1)
        path = match.group(2) or ''
        
        try:
            import pwd
            home = pwd.getpwnam(user).pw_dir
            return home + path
        except (ImportError, KeyError):
            return text
    
    return text

def expand_wildcards(text: str) -> list:
    """Expand wildcards in text"""
    import glob
    
    # Don't expand if quoted
    if is_quoted(text):
        return [strip_quotes(text)]
    
    # Perform expansion
    expanded = glob.glob(text)
    
    # Return original if no matches
    return expanded if expanded else [text]

def expand_all(text: str) -> str:
    """Perform all expansions on text"""
    # Handle quotes properly
    if text.startswith("'") and text.endswith("'"):
        # Single quotes prevent all expansion and are removed
        return text[1:-1]
    
    if text.startswith('"') and text.endswith('"'):
        # Double quotes allow variable and command expansion but not word splitting
        content = text[1:-1]
        result = expand_variables(content)
        
        # Handle arithmetic expansion inside double quotes (high priority)
        arith_pattern = r'\$\(\(([^()]*(?:\([^()]*\)[^()]*)*)\)\)'
        while re.search(arith_pattern, result):
            def expand_arith(match):
                return expand_arithmetic(match.group(0))
            result = re.sub(arith_pattern, expand_arith, result)
        
        # Handle command substitution inside double quotes
        cmd_pattern = r'\$\(([^()]*(?:\([^()]*\)[^()]*)*)\)'
        while re.search(cmd_pattern, result):
            def expand_cmd(match):
                return expand_command_substitution(match.group(0))
            result = re.sub(cmd_pattern, expand_cmd, result)
        
        # Handle backtick substitution inside double quotes
        backtick_pattern = r'`([^`]*(?:\\`[^`]*)*)`'
        while re.search(backtick_pattern, result):
            def expand_backtick(match):
                return expand_command_substitution(match.group(0))
            result = re.sub(backtick_pattern, expand_backtick, result)
            
        return result
    
    # For non-quoted text, do all expansions in proper order
    result = expand_variables(text)
    
    # Find and expand all arithmetic expansions (highest priority)
    arith_pattern = r'\$\(\(([^()]*(?:\([^()]*\)[^()]*)*)\)\)'
    while re.search(arith_pattern, result):
        def expand_arith(match):
            return expand_arithmetic(match.group(0))
        result = re.sub(arith_pattern, expand_arith, result)
    
    # Find and expand all command substitutions
    cmd_pattern = r'\$\(([^()]*(?:\([^()]*\)[^()]*)*)\)'
    while re.search(cmd_pattern, result):
        def expand_cmd(match):
            return expand_command_substitution(match.group(0))
        result = re.sub(cmd_pattern, expand_cmd, result)
    
    # Find and expand all backtick substitutions
    backtick_pattern = r'`([^`]*(?:\\`[^`]*)*)`'
    while re.search(backtick_pattern, result):
        def expand_backtick(match):
            return expand_command_substitution(match.group(0))
        result = re.sub(backtick_pattern, expand_backtick, result)
    
    # Tilde expansion after variable and command substitution
    result = expand_tilde(result)
    
    return result