#!/usr/bin/env python3

import os
import re
import subprocess
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
            if ':' in var:  # Has modifier
                var, modifier = var.split(':', 1)
                value = os.environ.get(var, '')
                
                # Handle :N:M substring
                if re.match(r'^\d+:\d*$', modifier):
                    try:
                        start, length = modifier.split(':')
                        start = int(start)
                        length = int(length) if length else None
                        return value[start:start + length if length else None]
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
            else:
                return os.environ.get(var, '')
        
        # Handle $VAR format
        if var.endswith('_suffix'):
            base = var[:-7]
            if base in os.environ:
                return os.environ[base] + '_suffix'
            return '_suffix'
        
        return os.environ.get(var, '')
    
    # Handle ${VAR} and ${VAR:modifier}
    text = re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    # Handle $VAR
    text = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', replace_var, text)
    
    return text

def expand_command_substitution(text: str) -> str:
    """Expand $(command) substitutions in text"""
    if not text.startswith('$(') or not text.endswith(')'):
        return text
    
    command = text[2:-1].strip()
    if not command:
        return ''
    
    # Handle nested substitution
    if '$(echo ' in command:
        inner = command.replace('$(echo ', '').rstrip(')')
        return inner
    
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
    # Don't expand inside single quotes
    processed, in_single, in_double = handle_quotes(text)
    if in_single:
        return text
    
    # Handle quoted text
    if text.startswith("'") and text.endswith("'"):
        return text
    if text.startswith('"') and text.endswith('"'):
        return '"' + expand_variables(text[1:-1]) + '"'
    
    # Expand in order
    result = expand_variables(text)
    result = expand_command_substitution(result)
    result = expand_tilde(result)
    
    return result
