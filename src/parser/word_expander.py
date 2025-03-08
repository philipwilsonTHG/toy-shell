#!/usr/bin/env python3

import os
import re
from typing import Optional, Callable, Dict, Any

from .expander import expand_all, expand_braces


class WordExpander:
    """
    Handles expansion of words including variables, braces, and other patterns.
    Separates expansion logic from the AST executor for better testability.
    """
    
    def __init__(self, scope_provider: Callable[[str], Optional[str]], debug_mode: bool = False):
        """
        Initialize the expander
        
        Args:
            scope_provider: A function that resolves variable names to values
            debug_mode: Whether to print debug information
        """
        self.scope_provider = scope_provider
        self.debug_mode = debug_mode
    
    def expand(self, word: str) -> str:
        """
        Expand variables, braces, and other patterns in a word
        
        Args:
            word: The word to expand
            
        Returns:
            The expanded word
        """
        # Single quotes prevent all expansion
        if word.startswith("'") and word.endswith("'"):
            return word
            
        # Check for brace expansion first
        if '{' in word:
            # Perform brace expansion
            brace_expansions = expand_braces(word)
            if len(brace_expansions) > 1:
                # Join the brace expansions with spaces
                expanded_word = ' '.join(brace_expansions)
                if self.debug_mode:
                    import sys
                    print(f"[DEBUG] Brace expansion: '{word}' -> '{expanded_word}'", file=sys.stderr)
                return expanded_word
        
        # Handle double quotes - expand content but preserve quotes
        is_double_quoted = word.startswith('"') and word.endswith('"')
        if is_double_quoted:
            content = word[1:-1]
            expanded = self._expand_variables(content)
            return f'"{expanded}"'
            
        # For normal unquoted words, expand everything
        return self._expand_variables(word)
    
    def _expand_variables(self, text: str) -> str:
        """Expand variables in the given text"""
        # Use regex to find variable references
        var_pattern = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_]*|\d+|[\*\@\#\?\$\!])')
        
        def replace_var(match):
            var_name = match.group(1)
            var_value = self.scope_provider(var_name)
            if self.debug_mode:
                import sys
                print(f"[DEBUG] Expanding ${var_name} to '{var_value}'", file=sys.stderr)
            return var_value or ''
            
        # Replace all variable references
        expanded = var_pattern.sub(replace_var, text)
        return expanded
    
    def handle_escaped_dollars(self, text: str) -> str:
        """
        Handle escaped dollar signs, converting escaped $ to $ for variable substitution
        
        Args:
            text: The text to process
        
        Returns:
            The text with escaped dollars converted
        """
        # Check for backslash-dollar sequences
        if '\\$' in text:
            return text.replace('\\$', '$')
        return text