#!/usr/bin/env python3

import os
import re
import sys
from typing import Optional, Callable, Dict, Any, List, Tuple, Match, Pattern, Set
from functools import lru_cache

from .expander import expand_braces


class WordExpander:
    """
    Handles expansion of words including variables, braces, and other patterns.
    Separates expansion logic from the AST executor for better testability.
    """
    
    # Precompile regex patterns for better performance
    VAR_PATTERN: Pattern = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_]*|\d+|[\*\@\#\?\$\!])')
    ARITH_PATTERN: Pattern = re.compile(r'\$\(\((.*?)\)\)')
    VAR_NAME_PATTERN: Pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)')
    
    def __init__(self, scope_provider: Callable[[str], Optional[str]], debug_mode: bool = False):
        """
        Initialize the expander
        
        Args:
            scope_provider: A function that resolves variable names to values
            debug_mode: Whether to print debug information
        """
        self.scope_provider = scope_provider
        self.debug_mode = debug_mode
        self.var_cache: Dict[str, Optional[str]] = {}
        self.expr_cache: Dict[str, str] = {}
        
    def debug_print(self, message: str) -> None:
        """Helper method for debug output"""
        if self.debug_mode:
            print(f"[DEBUG] {message}", file=sys.stderr)
    
    @lru_cache(maxsize=128)
    def expand(self, word: str) -> str:
        """
        Expand variables, braces, and other patterns in a word
        
        Args:
            word: The word to expand
            
        Returns:
            The expanded word
        """
        # Fast early returns for common cases
        if not word:
            return word
            
        # Single quotes prevent all expansion
        if word.startswith("'") and word.endswith("'"):
            return word
        
        # Check for commonly used expansions first
        needs_expansion = any(marker in word for marker in ('$', '{', '\\'))
        if not needs_expansion:
            return word
            
        # Check for brace expansion first (only when necessary)
        if '{' in word:
            return self._handle_brace_expansion(word)
        
        # Handle double quotes - expand content but preserve quotes
        is_double_quoted = word.startswith('"') and word.endswith('"')
        if is_double_quoted:
            content = word[1:-1]
            expanded = self._expand_variables(content)
            return f'"{expanded}"'
            
        # For normal unquoted words, expand everything
        return self._expand_variables(word)
    
    def _handle_brace_expansion(self, word: str) -> str:
        """Handle brace expansion with caching for repeated patterns"""
        # Perform brace expansion
        brace_expansions = expand_braces(word)
        if len(brace_expansions) > 1:
            # Join the brace expansions with spaces
            expanded_word = ' '.join(brace_expansions)
            self.debug_print(f"Brace expansion: '{word}' -> '{expanded_word}'")
            return expanded_word
        return self._expand_variables(word)
        
    def _expand_variables(self, text: str) -> str:
        """Expand variables in the given text using token-based approach"""
        # Check for arithmetic expressions first
        if ('$((' in text) and ('))' in text):
            text = self._expand_arithmetic(text)
        
        # Fast path for simple texts without $ vars
        if '$' not in text:
            return text
            
        # Tokenize the string for variable expansion
        tokens = self._tokenize_for_vars(text)
        
        # Process tokens
        result = []
        for token_type, token_text in tokens:
            if token_type == 'var':
                # It's a variable reference like $foo
                var_name = token_text[1:]  # Remove $ prefix
                var_value = self._get_var_value(var_name)
                result.append(var_value)
            else:
                # It's plain text
                result.append(token_text)
                
        return ''.join(result)
    
    def _tokenize_for_vars(self, text: str) -> List[Tuple[str, str]]:
        """
        Tokenize text into variables and literal text segments
        Returns a list of (type, text) tuples
        """
        # Use precompiled pattern and find all matches
        matches = list(self.VAR_PATTERN.finditer(text))
        
        if not matches:
            return [('text', text)]
            
        tokens = []
        last_end = 0
        
        for match in matches:
            start, end = match.span()
            
            # Add text before the variable
            if start > last_end:
                tokens.append(('text', text[last_end:start]))
                
            # Add the variable token
            tokens.append(('var', match.group(0)))
            last_end = end
            
        # Add any remaining text
        if last_end < len(text):
            tokens.append(('text', text[last_end:]))
            
        return tokens
    
    @lru_cache(maxsize=64)
    def _get_var_value(self, var_name: str) -> str:
        """Get a variable value with caching"""
        if var_name in self.var_cache:
            value = self.var_cache[var_name]
        else:
            value = self.scope_provider(var_name)
            self.var_cache[var_name] = value
            
        self.debug_print(f"Expanding ${var_name} to '{value}'")
        return value or ''
    
    def _clear_var_cache(self) -> None:
        """Clear the variable cache when variables change"""
        self.var_cache.clear()
        self._get_var_value.cache_clear()
        self.expand.cache_clear()
        
    def _expand_arithmetic(self, text: str) -> str:
        """
        Expand arithmetic expressions like $((expression)) in the given text
        with caching for repeated expressions
        
        Args:
            text: The text to process
            
        Returns:
            The text with arithmetic expressions evaluated
        """
        # Use cached results for the same text if available
        if text in self.expr_cache:
            return self.expr_cache[text]
            
        def evaluate_expression(match: Match) -> str:
            expression = match.group(1)
            
            # Check expression cache
            if expression in self.expr_cache:
                return self.expr_cache[expression]
                
            # Define local variables dictionary for the expression
            variables = {}
            
            # Extract variable names only once
            var_names = set(self.VAR_NAME_PATTERN.findall(expression))
            
            # Resolve each variable and add to our variables dictionary efficiently
            for var_name in var_names:
                var_value = self._get_var_value(var_name)
                try:
                    # Try to convert to number
                    variables[var_name] = int(var_value)
                except ValueError:
                    variables[var_name] = 0  # Default to 0 for non-numeric values
                        
            self.debug_print(f"Evaluating with variables: {variables}")
            
            try:
                # For safety, use a restricted evaluation context
                eval_context = variables.copy()
                
                # Evaluate the expression
                result = eval(expression, {"__builtins__": {}}, eval_context)
                
                self.debug_print(f"Evaluating arithmetic expression: '{expression}' -> {result}")
                
                result_str = str(result)
                # Cache this expression result
                self.expr_cache[expression] = result_str
                return result_str
            except Exception as e:
                self.debug_print(f"Error evaluating arithmetic expression: '{expression}': {e}")
                return "0"  # Default to 0 on error
        
        # Replace all arithmetic expressions
        result = self.ARITH_PATTERN.sub(evaluate_expression, text)
        
        # Cache the entire expanded result if it's not too large
        if len(text) < 1000:  # Only cache reasonably sized inputs
            self.expr_cache[text] = result
            
        return result
    
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