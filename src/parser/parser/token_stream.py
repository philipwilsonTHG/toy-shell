#!/usr/bin/env python3
"""
TokenStream class for managing a stream of tokens during parsing.
"""

from typing import List, Optional, NamedTuple
from ..token_types import Token, TokenType


class Position(NamedTuple):
    """Represents a position in the token stream."""
    index: int
    token: Optional[Token] = None


class TokenStream:
    """
    A stream of tokens that provides methods for consuming tokens and looking ahead.
    
    This class encapsulates the logic for traversing a list of tokens during parsing,
    providing methods for peeking ahead, consuming tokens, and matching expected tokens.
    """
    
    def __init__(self, tokens: List[Token]):
        """Initialize a new token stream with the given tokens."""
        self.tokens = tokens
        self.current = 0
    
    def peek(self, offset: int = 0) -> Optional[Token]:
        """
        Look ahead in the token stream without consuming the token.
        
        Args:
            offset: How many tokens ahead to look (default: 0, the current token)
            
        Returns:
            The token at the current position + offset, or None if out of range
        """
        # Safety checks to prevent infinite loops and invalid indices
        if not self.tokens:
            return None
            
        if self.current < 0:
            self.current = 0
            
        if self.current >= len(self.tokens):
            return None
            
        if self.current + offset >= len(self.tokens):
            return None
            
        # Now it's safe to access the token
        return self.tokens[self.current + offset]
    
    def current_position(self) -> Position:
        """
        Get the current position in the token stream.
        
        Returns:
            A Position object with the current index and token
        """
        # Safety check for current pointer
        current = self.current
        if current < 0:
            current = 0
        if current > len(self.tokens):
            current = len(self.tokens)
            
        return Position(
            index=current,
            token=self.peek()  # peek has its own safety checks
        )
    
    def consume(self) -> Optional[Token]:
        """
        Consume the current token and advance the stream.
        
        Returns:
            The token that was consumed, or None if at the end of the stream
        """
        if self.is_at_end():
            return None
        
        # Safety check: if current is somehow negative, reset to beginning
        if self.current < 0:
            self.current = 0
        
        # Get the token
        token = self.tokens[self.current]
        
        # Advance the pointer (with safety check for maximum)
        self.current += 1
        if self.current > len(self.tokens):
            self.current = len(self.tokens)
            
        return token
    
    def match(self, token_type: TokenType, value: Optional[str] = None) -> bool:
        """
        Check if the current token matches the expected type and value,
        and consume it if it does.
        
        Args:
            token_type: The expected token type
            value: The expected token value (if None, only the type is checked)
            
        Returns:
            True if the token matched and was consumed, False otherwise
        """
        if self.is_at_end():
            return False
            
        token = self.peek()
        if token.token_type != token_type:
            return False
            
        if value is not None and token.value != value:
            return False
            
        # It's a match, consume the token
        self.consume()
        return True
    
    def match_any(self, token_types: List[TokenType]) -> bool:
        """
        Check if the current token matches any of the expected types,
        and consume it if it does.
        
        Args:
            token_types: A list of expected token types
            
        Returns:
            True if the token matched any type and was consumed, False otherwise
        """
        if self.is_at_end():
            return False
            
        token = self.peek()
        if token.token_type not in token_types:
            return False
            
        # It's a match, consume the token
        self.consume()
        return True
    
    def match_keyword(self, keyword: str) -> bool:
        """
        Check if the current token is a keyword with the given value,
        and consume it if it is.
        
        Args:
            keyword: The expected keyword value
            
        Returns:
            True if the token was a matching keyword and was consumed, False otherwise
        """
        return self.match(TokenType.KEYWORD, keyword)
    
    def match_operator(self, operator: str) -> bool:
        """
        Check if the current token is an operator with the given value,
        and consume it if it is.
        
        Args:
            operator: The expected operator value
            
        Returns:
            True if the token was a matching operator and was consumed, False otherwise
        """
        return self.match(TokenType.OPERATOR, operator)
    
    def is_at_end(self) -> bool:
        """
        Check if we've reached the end of the token stream.
        
        Returns:
            True if there are no more tokens to consume, False otherwise
        """
        return self.current >= len(self.tokens)
    
    def save_position(self) -> int:
        """
        Save the current position in the token stream for later restoration.
        
        Returns:
            The current position index
        """
        return self.current
    
    def restore_position(self, position: int) -> None:
        """
        Restore the stream to a previously saved position.
        
        Args:
            position: A position index returned by save_position()
        """
        # Safety bounds checks to prevent infinite loops
        if position < 0:
            position = 0
        elif position > len(self.tokens):
            position = len(self.tokens)
            
        self.current = position