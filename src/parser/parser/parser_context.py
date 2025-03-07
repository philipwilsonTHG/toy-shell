#!/usr/bin/env python3
"""
ParserContext class for maintaining state and error handling during parsing.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .token_stream import Position


@dataclass
class ParseError:
    """
    Represents an error that occurred during parsing.
    """
    message: str
    position: Position
    suggestion: Optional[str] = None


class ParserContext:
    """
    Context object that maintains state and provides services during parsing.
    
    This class keeps track of errors, symbol tables, and other context needed
    during parsing. It provides an abstraction for error reporting and recovery.
    """
    
    def __init__(self):
        """Initialize a new parser context."""
        self.errors: List[ParseError] = []
        self.warnings: List[ParseError] = []
        self.scopes: List[Dict[str, Any]] = [{}]  # Start with global scope
        self.in_progress: bool = False  # For tracking multi-line input
        self.recovery_mode: bool = False
        
    def report_error(self, message: str, position: Position, suggestion: Optional[str] = None):
        """
        Report an error that occurred during parsing.
        
        Args:
            message: A description of the error
            position: The position where the error occurred
            suggestion: Optional suggestion for fixing the error
        """
        error = ParseError(message, position, suggestion)
        self.errors.append(error)
        
    def report_warning(self, message: str, position: Position, suggestion: Optional[str] = None):
        """
        Report a warning that occurred during parsing.
        
        Args:
            message: A description of the warning
            position: The position where the warning occurred
            suggestion: Optional suggestion for fixing the warning
        """
        warning = ParseError(message, position, suggestion)
        self.warnings.append(warning)
        
    def enter_scope(self) -> None:
        """Enter a new scope for variable bindings."""
        self.scopes.append({})
        
    def exit_scope(self) -> None:
        """Exit the current scope."""
        if len(self.scopes) > 1:
            self.scopes.pop()
            
    def define(self, name: str, value: Any) -> None:
        """
        Define a variable in the current scope.
        
        Args:
            name: The name of the variable
            value: The value to associate with the name
        """
        self.scopes[-1][name] = value
        
    def lookup(self, name: str) -> Optional[Any]:
        """
        Look up a variable in the current scope chain.
        
        Args:
            name: The name of the variable to look up
            
        Returns:
            The value associated with the name, or None if not found
        """
        # Search from innermost scope outward
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def current_scope(self) -> Dict[str, Any]:
        """
        Get the current innermost scope.
        
        Returns:
            The current scope dictionary
        """
        return self.scopes[-1]
    
    def has_errors(self) -> bool:
        """
        Check if any errors were reported.
        
        Returns:
            True if errors were reported, False otherwise
        """
        return len(self.errors) > 0
    
    def mark_in_progress(self, value: bool = True) -> None:
        """
        Mark the parsing as in progress or complete.
        
        Args:
            value: True if parsing is in progress, False if complete
        """
        self.in_progress = value
        
    def is_in_progress(self) -> bool:
        """
        Check if parsing is in progress.
        
        Returns:
            True if parsing is in progress, False if complete
        """
        return self.in_progress
    
    def enter_recovery_mode(self) -> None:
        """Enter error recovery mode."""
        self.recovery_mode = True
        
    def exit_recovery_mode(self) -> None:
        """Exit error recovery mode."""
        self.recovery_mode = False
        
    def in_recovery_mode(self) -> bool:
        """
        Check if we're in error recovery mode.
        
        Returns:
            True if in recovery mode, False otherwise
        """
        return self.recovery_mode
    
    def format_errors(self) -> str:
        """
        Format all errors for display.
        
        Returns:
            A formatted string representation of all errors
        """
        if not self.errors:
            return "No errors."
            
        result = []
        for i, error in enumerate(self.errors):
            position_info = f"token #{error.position.index}"
            if error.position.token:
                position_info += f" '{error.position.token.value}'"
                
            result.append(f"Error {i+1}: {error.message} at {position_info}")
            if error.suggestion:
                result.append(f"  Suggestion: {error.suggestion}")
                
        return "\n".join(result)