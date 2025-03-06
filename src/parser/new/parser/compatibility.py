#!/usr/bin/env python3
"""
Compatibility layer for the new parser implementation.

This module provides adapter functions to make the new parser API
compatible with the old parser API, so the rest of the code
can work without changes during the transition period.
"""

import warnings
from typing import Optional, List

from ....parser.ast import Node
from ..token_types import Token
from .shell_parser import ShellParser


class Parser:
    """
    Adapter class that mimics the interface of the old Parser class.
    
    This class is a thin wrapper around the new ShellParser to provide
    the same API as the old Parser class.
    """
    
    def __init__(self):
        """Initialize a new parser adapter."""
        self.parser = ShellParser()
        
    def parse(self, line: str) -> Optional[Node]:
        """
        Parse a line of input into an AST.
        
        Args:
            line: The line to parse
            
        Returns:
            The root AST node, or None if parsing failed or is incomplete
        """
        return self.parser.parse_multi_line(line)
    
    def is_incomplete(self) -> bool:
        """
        Check if the parser is waiting for more input.
        
        Returns:
            True if parsing is incomplete, False otherwise
        """
        return self.parser.is_incomplete()
    
    def reset(self) -> None:
        """Reset the parser state."""
        self.parser = ShellParser()


def get_parser() -> Parser:
    """
    Get a parser instance that uses the new implementation.
    
    This function is used by the old code to get a parser instance,
    but it returns a parser that uses the new implementation.
    
    Returns:
        A Parser instance that uses the new implementation
    """
    warnings.warn(
        "Using the old Parser API. Consider migrating to the new parser API.",
        DeprecationWarning,
        stacklevel=2
    )
    return Parser()