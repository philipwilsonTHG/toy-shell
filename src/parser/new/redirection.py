#!/usr/bin/env python3

from typing import List, Tuple, Dict, Optional
from .token_types import Token, TokenType

class RedirectionType:
    """Constants for redirection types"""
    STDOUT = ">"            # Redirect stdout to file
    STDOUT_APPEND = ">>"    # Append stdout to file
    STDIN = "<"             # Read stdin from file
    STDERR = "2>"           # Redirect stderr to file
    STDERR_APPEND = "2>>"   # Append stderr to file
    STDERR_TO_STDOUT = "2>&1"  # Redirect stderr to stdout
    FD_REF = "&1"           # Reference to stdout file descriptor

class RedirectionParser:
    """Handles parsing and normalization of shell redirections"""
    
    @staticmethod
    def is_redirection(token: Token) -> bool:
        """Check if token is a redirection operator"""
        if token.token_type != TokenType.OPERATOR:
            return False
        
        # Check basic redirections
        if token.value in {
            RedirectionType.STDOUT, 
            RedirectionType.STDOUT_APPEND,
            RedirectionType.STDIN,
            RedirectionType.STDERR,
            RedirectionType.STDERR_APPEND
        }:
            return True
            
        # Check file descriptor reference
        if token.value == RedirectionType.FD_REF:
            return True
            
        return False
    
    @staticmethod
    def parse_redirections(tokens: List[Token]) -> Tuple[List[Token], List[Tuple[str, str]]]:
        """
        Extract redirections from token list
        
        Args:
            tokens: List of tokens to parse
            
        Returns:
            tuple containing:
            - List of remaining tokens after removing redirections
            - List of redirections as (operator, target) tuples
        """
        result = []
        redirections = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if RedirectionParser.is_redirection(token):
                # Handle special case for 2>&1 redirection
                if token.value == RedirectionType.STDERR and i + 1 < len(tokens) and tokens[i + 1].value == RedirectionType.FD_REF:
                    # Use special format for this redirection
                    redirections.append((RedirectionType.STDERR_TO_STDOUT, ""))
                    i += 2
                else:
                    # Normal redirections require a target
                    if i + 1 >= len(tokens):
                        raise ValueError(f"Missing target for redirection {token.value}")
                    redirections.append((token.value, tokens[i + 1].value))
                    i += 2
            else:
                result.append(token)
                i += 1
        
        return result, redirections
    
    @staticmethod
    def split_pipeline(tokens: List[Token]) -> List[List[Token]]:
        """Split tokens into pipeline segments at pipe (|) operators"""
        segments = []
        current = []
        
        for token in tokens:
            if token.token_type == TokenType.OPERATOR and token.value == '|':
                if current:
                    segments.append(current)
                    current = []
            else:
                current.append(token)
        
        if current:
            segments.append(current)
        
        return segments