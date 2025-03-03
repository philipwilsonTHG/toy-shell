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

def expand_command_substitution(text: str) -> str:
    """Expand $(command) substitutions in text"""
    if not text.startswith('$(') or not text.endswith(')'):
        return text
    
    command = text[2:-1].strip()
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
        
        # Handle command substitution inside double quotes
        cmd_pattern = r'\$\(([^()]*(?:\([^()]*\)[^()]*)*)\)'
        while re.search(cmd_pattern, result):
            def expand_cmd(match):
                return expand_command_substitution(match.group(0))
            result = re.sub(cmd_pattern, expand_cmd, result)
            
        return result
    
    # For non-quoted text, do all expansions in proper order
    result = expand_variables(text)
    
    # Find and expand all command substitutions
    cmd_pattern = r'\$\(([^()]*(?:\([^()]*\)[^()]*)*)\)'
    while re.search(cmd_pattern, result):
        def expand_cmd(match):
            return expand_command_substitution(match.group(0))
        result = re.sub(cmd_pattern, expand_cmd, result)
    
    # Tilde expansion after variable and command substitution
    result = expand_tilde(result)
    
    return result