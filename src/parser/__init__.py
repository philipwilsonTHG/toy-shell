"""
Command parsing and lexical analysis

IMPORTANT: The lexer API has moved to specific modules.

Please use these direct imports instead:
- from src.parser.new.token_types import Token, TokenType
- from src.parser.new.lexer import tokenize
- from src.parser.new.redirection import RedirectionParser

See docs/migration_guide.md for details on migrating to the new API.
"""

import warnings

warnings.warn(
    "The src.parser module no longer provides lexer functionality. "
    "Use src.parser.new.token_types, src.parser.new.lexer, and src.parser.new.redirection directly. "
    "See docs/migration_guide.md for details.",
    ImportWarning,
    stacklevel=2
)

# Import expander & quotes modules which are still supported here
from .expander import expand_variables, expand_command_substitution
from .quotes import handle_quotes, is_quoted, strip_quotes

__all__ = [
    'expand_variables',
    'expand_command_substitution',
    'handle_quotes',
    'is_quoted',
    'strip_quotes',
]
