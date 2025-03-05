#!/usr/bin/env python3

from .token_types import Token, TokenType
from .lexer import tokenize as new_tokenize
from .redirection import RedirectionParser, RedirectionType

# For direct use of the new API
__all__ = [
    'Token', 'TokenType', 'new_tokenize',
    'RedirectionParser', 'RedirectionType'
]

# Expose compatibility functions with the same names as the old API
from .compatibility import tokenize, parse_redirections, split_pipeline

# Add compatibility functions to exports
__all__.extend(['tokenize', 'parse_redirections', 'split_pipeline'])