#!/usr/bin/env python3
"""
Adapter class for the state machine expander to maintain compatibility
with the existing WordExpander interface.
"""

from typing import Optional, Callable, Dict

from .state_machine_expander import StateMachineExpander


class StateMachineWordExpander:
    """
    Adapter class that makes StateMachineExpander compatible with the existing WordExpander interface.
    This allows for easy drop-in replacement of the current expander with our state machine implementation.
    """
    
    def __init__(self, scope_provider: Callable[[str], Optional[str]], debug_mode: bool = False):
        """
        Initialize the expander
        
        Args:
            scope_provider: A function that resolves variable names to values
            debug_mode: Whether to print debug information
        """
        self.expander = StateMachineExpander(scope_provider, debug_mode)
        self.debug_mode = debug_mode
        self.var_cache: Dict[str, str] = {}
    
    def expand(self, word: str) -> str:
        """
        Expand variables, braces, and other patterns in a word
        
        Args:
            word: The word to expand
            
        Returns:
            The expanded word
        """
        # First check if this is a single-quoted string (for compatibility with original)
        if word.startswith("'") and word.endswith("'"):
            return word
        
        # Check if this is a double-quoted string with inner quotes - special handling needed
        if word.startswith('"') and word.endswith('"') and "'" in word:
            # Preserve the inner single quotes during expansion
            content = word[1:-1]
            expanded = self.expander.expand(content)
            
            # If the inner single quotes were lost, we need to reinsert them
            # This handles cases like: "outer 'inner' quotes"
            if "'" in content and "'" not in expanded:
                # Re-insert the inner quotes that might have been removed
                for i, char in enumerate(content):
                    if char == "'" and expanded[i] != "'":
                        expanded = expanded[:i] + "'" + expanded[i:]
            
            return expanded
            
        return self.expander.expand(word)
    
    def _expand_variables(self, text: str) -> str:
        """
        Legacy method for compatibility - uses the state machine expander internally
        """
        return self.expander.expand_unquoted(text)
    
    def _expand_arithmetic(self, text: str) -> str:
        """
        Legacy method for compatibility - not used directly
        """
        if text.startswith('$((') and text.endswith('))'):
            # Use private method of expander for compatibility
            # pylint: disable=protected-access
            return self.expander._expand_arithmetic(text)
        return self.expander.expand(text)
    
    def handle_escaped_dollars(self, text: str) -> str:
        """
        Handle escaped dollar signs, converting escaped $ to $ for variable substitution
        
        Args:
            text: The text to process
        
        Returns:
            The text with escaped dollars converted
        """
        # This is handled by the state machine expander, but kept for compatibility
        if '\\$' in text:
            return text.replace('\\$', '$')
        return text
    
    def _clear_var_cache(self) -> None:
        """Clear the variable cache when variables change"""
        self.expander.clear_caches()
        self.var_cache.clear()