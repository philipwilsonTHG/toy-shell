#!/usr/bin/env python3

"""
Compatibility layer for the new lexer implementation.
This module provides adapter functions to make the new lexer API
compatible with the old lexer API, so the rest of the code 
can work without changes.
"""

from typing import List, Tuple, Dict, Optional, Any
from .token_types import Token as NewToken, TokenType
from .lexer import tokenize as new_tokenize
from .redirection import RedirectionParser

# Legacy Token class for backward compatibility
class Token:
    """Represents a shell token with type information"""
    
    def __init__(self, value: str, token_type: str = 'word'):
        self.value = value
        self.type = token_type
        self.quoted = False  # Track if this token was originally quoted
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        if hasattr(self, 'quoted') and self.quoted:
            return f"Token({self.value!r}, {self.type!r}, quoted=True)"
        return f"Token({self.value!r}, {self.type!r})"

# Legacy function for removing quotes
def remove_quotes(token: str) -> str:
    """Remove surrounding quotes from a token if present"""
    if len(token) >= 2:
        if (token[0] == '"' and token[-1] == '"') or (token[0] == "'" and token[-1] == "'"):
            return token[1:-1]
    return token

# Legacy function to check if a token is a redirection operator
def is_redirection(token: Token) -> bool:
    """Check if token is a redirection operator"""
    if token.type != 'operator':
        return False
    # Match basic redirections
    if token.value in {'>', '<', '>>', '<<', '>&', '<&'}:
        return True
    # Match stderr redirections
    if token.value in {'2>', '2>>'}:
        return True
    # Handle &1 (file descriptor reference) as part of a redirection
    if token.value == '&1':
        return True
    return False

def adapt_token_type(token_type: TokenType) -> str:
    """Convert new TokenType enum to old token type string"""
    return token_type.value

def create_legacy_token(token: NewToken) -> Token:
    """Create a token compatible with the legacy Token class"""
    legacy_token = Token(token.value, adapt_token_type(token.token_type))
    if token.quoted:
        legacy_token.quoted = True
    
    return legacy_token

def tokenize(line: str) -> List[Any]:
    """Tokenize a line using the new lexer, but return tokens compatible with the old API"""
    new_tokens = new_tokenize(line)
    return [create_legacy_token(token) for token in new_tokens]

def parse_redirections(tokens: List[Token]) -> Tuple[List[Token], List[Tuple[str, str]]]:
    """Parse redirections using the new parser, but with compatibility for old tokens"""
    # Convert legacy tokens to new tokens
    new_tokens = []
    for token in tokens:
        token_type = TokenType.OPERATOR if token.type == 'operator' else \
                     TokenType.KEYWORD if token.type == 'keyword' else \
                     TokenType.SUBSTITUTION if token.type == 'substitution' else \
                     TokenType.WORD
        
        new_token = NewToken(token.value, token_type)
        if hasattr(token, 'quoted'):
            new_token.quoted = token.quoted
        
        new_tokens.append(new_token)
    
    # Parse redirections using new parser
    cmd_tokens, redirections = RedirectionParser.parse_redirections(new_tokens)
    
    # Convert new tokens back to legacy tokens
    legacy_cmd_tokens = [create_legacy_token(token) for token in cmd_tokens]
    
    return legacy_cmd_tokens, redirections

def split_pipeline(tokens: List[Token]) -> List[List[Token]]:
    """Split a pipeline using the new parser, but with compatibility for old tokens"""
    # Convert legacy tokens to new tokens
    new_tokens = []
    for token in tokens:
        token_type = TokenType.OPERATOR if token.type == 'operator' else \
                     TokenType.KEYWORD if token.type == 'keyword' else \
                     TokenType.SUBSTITUTION if token.type == 'substitution' else \
                     TokenType.WORD
        
        new_token = NewToken(token.value, token_type)
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