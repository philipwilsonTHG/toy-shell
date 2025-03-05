#!/usr/bin/env python3

"""
Compatibility layer for the new lexer implementation.
This module provides adapter functions to make the new lexer API
compatible with the old lexer API, so the rest of the code 
can work without changes.
"""

from typing import List, Tuple, Dict, Optional, Any
from .token_types import Token, TokenType
from .lexer import tokenize as new_tokenize
from .redirection import RedirectionParser

def adapt_token_type(token_type: TokenType) -> str:
    """Convert new TokenType enum to old token type string"""
    return token_type.value

def create_legacy_token(token: Token) -> Any:
    """Create a token compatible with the old Token class"""
    from ..lexer import Token as LegacyToken
    
    legacy_token = LegacyToken(token.value, adapt_token_type(token.token_type))
    if token.quoted:
        legacy_token.quoted = True
    
    return legacy_token

def tokenize(line: str) -> List[Any]:
    """Tokenize a line using the new lexer, but return tokens compatible with the old API"""
    new_tokens = new_tokenize(line)
    return [create_legacy_token(token) for token in new_tokens]

def parse_redirections(tokens: List[Any]) -> Tuple[List[Any], List[Tuple[str, str]]]:
    """Parse redirections using the new parser, but with compatibility for old tokens"""
    # Convert legacy tokens to new tokens
    new_tokens = []
    for token in tokens:
        token_type = TokenType.OPERATOR if token.type == 'operator' else \
                     TokenType.KEYWORD if token.type == 'keyword' else \
                     TokenType.SUBSTITUTION if token.type == 'substitution' else \
                     TokenType.WORD
        
        new_token = Token(token.value, token_type)
        if hasattr(token, 'quoted'):
            new_token.quoted = token.quoted
        
        new_tokens.append(new_token)
    
    # Parse redirections using new parser
    cmd_tokens, redirections = RedirectionParser.parse_redirections(new_tokens)
    
    # Convert new tokens back to legacy tokens
    legacy_cmd_tokens = [create_legacy_token(token) for token in cmd_tokens]
    
    return legacy_cmd_tokens, redirections

def split_pipeline(tokens: List[Any]) -> List[List[Any]]:
    """Split a pipeline using the new parser, but with compatibility for old tokens"""
    # Convert legacy tokens to new tokens
    new_tokens = []
    for token in tokens:
        token_type = TokenType.OPERATOR if token.type == 'operator' else \
                     TokenType.KEYWORD if token.type == 'keyword' else \
                     TokenType.SUBSTITUTION if token.type == 'substitution' else \
                     TokenType.WORD
        
        new_token = Token(token.value, token_type)
        if hasattr(token, 'quoted'):
            new_token.quoted = token.quoted
        
        new_tokens.append(new_token)
    
    # Split pipeline using new parser
    segments = RedirectionParser.split_pipeline(new_tokens)
    
    # Convert new tokens back to legacy tokens
    legacy_segments = []
    for segment in segments:
        legacy_segment = [create_legacy_token(token) for token in segment]
        legacy_segments.append(legacy_segment)
    
    return legacy_segments