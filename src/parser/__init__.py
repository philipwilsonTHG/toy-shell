"""
Command parsing and lexical analysis
"""

# Import old modules for backward compatibility
from .expander import expand_variables, expand_command_substitution
from .quotes import handle_quotes, is_quoted, strip_quotes

# Choose which implementation to use - comment one and uncomment the other

# Use the original lexer implementation:
# from .lexer import tokenize, remove_quotes, parse_redirections, split_pipeline, Token, is_redirection

# Use the new lexer implementation through the compatibility layer:
from .new.compatibility import tokenize, parse_redirections, split_pipeline
from .lexer import Token, remove_quotes, is_redirection

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
