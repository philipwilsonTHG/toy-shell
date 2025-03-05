#!/usr/bin/env python3

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any

class TokenType(Enum):
    """Types of tokens in shell syntax"""
    WORD = "word"             # Normal words/arguments
    OPERATOR = "operator"     # Operators like |, &, ;
    KEYWORD = "keyword"       # Shell keywords like if, while, for
    SUBSTITUTION = "substitution"  # Command substitution like $() or ``
    REDIRECTION = "redirection"  # Redirection operators

@dataclass
class Token:
    """Base token class with type information"""
    value: str
    token_type: TokenType = TokenType.WORD
    quoted: bool = False
    
    def __str__(self) -> str:
        """String representation, useful for reconstructing the command"""
        return self.value
    
    def __repr__(self) -> str:
        """Debug representation showing token type and quoting information"""
        if self.quoted:
            return f"Token({self.value!r}, {self.token_type}, quoted=True)"
        return f"Token({self.value!r}, {self.token_type})"
    
    def is_type(self, token_type: TokenType) -> bool:
        """Check if token is of the specified type"""
        return self.token_type == token_type
    
    def is_operator(self, value: Optional[str] = None) -> bool:
        """Check if token is an operator, optionally of specific value"""
        if self.token_type != TokenType.OPERATOR:
            return False
        if value is not None:
            return self.value == value
        return True
    
    def is_keyword(self, value: Optional[str] = None) -> bool:
        """Check if token is a keyword, optionally of specific value"""
        if self.token_type != TokenType.KEYWORD:
            return False
        if value is not None:
            return self.value == value
        return True
    
    def is_word(self) -> bool:
        """Check if token is a normal word"""
        return self.token_type == TokenType.WORD

# Standard shell keywords
KEYWORDS = {
    'if': TokenType.KEYWORD,
    'then': TokenType.KEYWORD,
    'else': TokenType.KEYWORD,
    'elif': TokenType.KEYWORD,
    'fi': TokenType.KEYWORD,
    'while': TokenType.KEYWORD,
    'until': TokenType.KEYWORD,
    'for': TokenType.KEYWORD,
    'in': TokenType.KEYWORD,
    'do': TokenType.KEYWORD,
    'done': TokenType.KEYWORD,
    'case': TokenType.KEYWORD,
    'esac': TokenType.KEYWORD,
    'function': TokenType.KEYWORD,
}

def create_keyword_token(value: str) -> Token:
    """Create a token for a shell keyword"""
    if value not in KEYWORDS:
        raise ValueError(f"Unknown keyword: {value}")
    return Token(value, TokenType.KEYWORD)

def create_operator_token(value: str) -> Token:
    """Create a token for a shell operator"""
    return Token(value, TokenType.OPERATOR)

def create_word_token(value: str, quoted: bool = False) -> Token:
    """Create a token for a normal word, optionally quoted"""
    token = Token(value, TokenType.WORD)
    token.quoted = quoted
    return token

def create_substitution_token(value: str) -> Token:
    """Create a token for a command substitution"""
    return Token(value, TokenType.SUBSTITUTION)