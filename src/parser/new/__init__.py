#!/usr/bin/env python3

from .token_types import Token, TokenType
from .lexer import tokenize as new_tokenize
from .redirection import RedirectionParser, RedirectionType

# Direct exports of the new API
__all__ = [
    'Token', 'TokenType', 'new_tokenize',
    'RedirectionParser', 'RedirectionType'
]

# Note: We no longer expose compatibility functions here
# Clients should use the direct imports instead:
# - from src.parser.new.token_types import Token, TokenType
# - from src.parser.new.lexer import tokenize
# - from src.parser.new.redirection import RedirectionParser