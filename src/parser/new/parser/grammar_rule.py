#!/usr/bin/env python3
"""
Base class for grammar rules in the parser.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Set

from ....parser.ast import Node
from ..token_types import TokenType
from .token_stream import TokenStream
from .parser_context import ParserContext


class GrammarRule(ABC):
    """
    Abstract base class for all grammar rules in the parser.
    
    Each concrete rule implements the parse method to handle a specific grammar construct.
    """
    
    @abstractmethod
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a grammar construct from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A node representing the parsed construct, or None if parsing failed
        """
        pass
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        This is used for predictive parsing to determine which rule to apply.
        
        Returns:
            A set of token types that this rule can start with
        """
        return set()
    
    def can_start_with_keyword(self, keyword: str) -> bool:
        """
        Check if this rule can start with the given keyword.
        
        Args:
            keyword: The keyword to check
            
        Returns:
            True if this rule can start with the given keyword, False otherwise
        """
        return False
    
    def can_start_with_operator(self, operator: str) -> bool:
        """
        Check if this rule can start with the given operator.
        
        Args:
            operator: The operator to check
            
        Returns:
            True if this rule can start with the given operator, False otherwise
        """
        return False
    
    def skip_to_sync_point(self, stream: TokenStream, context: ParserContext, 
                          sync_points: List[str]) -> None:
        """
        Skip tokens until a synchronization point is reached.
        
        This is used for error recovery to skip past invalid tokens.
        
        Args:
            stream: The token stream to skip in
            context: The parser context for state and error reporting
            sync_points: A list of keywords or operators to synchronize on
        """
        while not stream.is_at_end():
            token = stream.peek()
            
            # Check if we've reached a sync point
            if token.token_type == TokenType.KEYWORD and token.value in sync_points:
                return
                
            if token.token_type == TokenType.OPERATOR and token.value in sync_points:
                return
                
            # Skip this token
            stream.consume()