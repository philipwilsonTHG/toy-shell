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
        # Check for arithmetic expressions first
        result = self._expand_arithmetic(text)
        
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
        expanded = var_pattern.sub(replace_var, result)
        return expanded
        
    def _expand_arithmetic(self, text: str) -> str:
        """
        Expand arithmetic expressions like $((expression)) in the given text
        
        Args:
            text: The text to process
            
        Returns:
            The text with arithmetic expressions evaluated
        """
        # Pattern for matching arithmetic expressions
        arith_pattern = re.compile(r'\$\(\((.*?)\)\)')
        
        def evaluate_expression(match):
            expression = match.group(1)
            
            # Define local variables dictionary for the expression
            variables = {}
            
            # Extract variable names from the expression (without $ prefix)
            var_names = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', expression)
            
            # Resolve each variable and add to our variables dictionary
            for var_name in var_names:
                var_value = self.scope_provider(var_name)
                if var_value is None:
                    variables[var_name] = 0  # Default to 0 for undefined variables
                else:
                    try:
                        # Try to convert to number
                        variables[var_name] = int(var_value)
                    except ValueError:
                        variables[var_name] = 0  # Default to 0 for non-numeric values
                        
            # Use the variables in expression evaluation context
            if self.debug_mode:
                import sys
                print(f"[DEBUG] Evaluating with variables: {variables}", file=sys.stderr)
            
            try:
                # For safety, we'll parse and evaluate the expression manually using the variables
                # First, provide the correct variables for the context
                eval_context = variables.copy()
                
                # Evaluate the expression
                result = eval(expression, {"__builtins__": {}}, eval_context)
                
                if self.debug_mode:
                    import sys
                    print(f"[DEBUG] Evaluating arithmetic expression: '{expression}' -> {result}", file=sys.stderr)
                
                return str(result)
            except Exception as e:
                if self.debug_mode:
                    import sys
                    print(f"[DEBUG] Error evaluating arithmetic expression: '{expression}': {e}", file=sys.stderr)
                return "0"  # Default to 0 on error
        
        # Replace all arithmetic expressions
        return arith_pattern.sub(evaluate_expression, text)
    
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