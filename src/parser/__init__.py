"""
Command parsing and lexical analysis

This module provides the parser for shell scripts, with a modern implementation
using grammar rules and better error handling.
"""

import warnings

# Import expander & quotes modules which are still supported here
from .expander import expand_variables, expand_command_substitution
from .quotes import handle_quotes, is_quoted, strip_quotes

# Import the new implementation through the compatibility layer
warnings.warn(
    "The parser module is transitioning to a new implementation. "
    "For new code, consider using the new parser API directly: "
    "from src.parser.new.parser import ShellParser",
    DeprecationWarning,
    stacklevel=2
)

# For backward compatibility, we still provide the Parser class
from .parser import Parser

# Export the public API
__all__ = [
    'Parser',
    'expand_variables',
    'expand_command_substitution',
    'handle_quotes',
    'is_quoted',
    'strip_quotes',
]