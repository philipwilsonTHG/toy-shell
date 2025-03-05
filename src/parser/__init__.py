"""
Command parsing and lexical analysis
"""

# Import expander & quotes modules for backward compatibility
from .expander import expand_variables, expand_command_substitution
from .quotes import handle_quotes, is_quoted, strip_quotes

# Import our new lexer implementation through the compatibility layer
# This provides all the functionality of the old lexer but with better code organization
from .new.compatibility import (
    tokenize, parse_redirections, split_pipeline,
    Token, remove_quotes, is_redirection
)

__all__ = [
    'tokenize',
    'remove_quotes',
    'expand_variables',
    'expand_command_substitution',
    'handle_quotes',
    'is_quoted',
    'strip_quotes',
    'parse_redirections',
    'split_pipeline',
    'Token',
    'is_redirection'
]
