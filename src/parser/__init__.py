"""
Command parsing and lexical analysis

DEPRECATED IMPORT PATH: Importing from src.parser is deprecated.

Please use these direct imports instead:
- from src.parser.new.token_types import Token, TokenType
- from src.parser.new.lexer import tokenize
- from src.parser.new.redirection import RedirectionParser

See docs/migration_guide.md for details on migrating to the new API.
"""

import warnings

warnings.warn(
    "Importing lexer components from src.parser is deprecated. "
    "Use src.parser.new.token_types, src.parser.new.lexer, and src.parser.new.redirection directly. "
    "See docs/migration_guide.md for details.",
    DeprecationWarning,
    stacklevel=2
)

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
