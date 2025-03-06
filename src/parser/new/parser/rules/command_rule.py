#!/usr/bin/env python3
"""
Rule for parsing simple commands.
"""

from typing import List, Set, Tuple, Optional

from .....parser.ast import Node, CommandNode
from ...token_types import Token, TokenType
from ..grammar_rule import GrammarRule
from ..token_stream import TokenStream, Position
from ..parser_context import ParserContext


class CommandRule(GrammarRule):
    """
    Rule for parsing simple commands like "echo hello" or "ls -la".
    
    A command consists of a command name followed by arguments,
    optional redirections, and an optional background flag.
    """
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        Returns:
            A set containing TokenType.WORD and TokenType.SUBSTITUTION
        """
        return {TokenType.WORD, TokenType.SUBSTITUTION}
    
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a simple command from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A CommandNode representing the command, or None if parsing failed
        """
        # Check if we can parse a command
        if stream.is_at_end():
            return None
            
        # Save the current position in case we need to backtrack
        start_pos = stream.save_position()
        
        # Get the command name and arguments
        args = []
        redirections = []
        background = False
        
        # Parse the command and its arguments - with safety checks
        # Maximum number of tokens to consume - avoid infinite loops
        max_tokens = len(stream.tokens) * 2  # Set a generous safety limit
        token_count = 0
        
        while not stream.is_at_end() and token_count < max_tokens:
            token_count += 1
            token = stream.peek()
            
            if token is None:
                # Safety check - sometimes peek can return None in error conditions
                break
                
            # Check for command terminators
            if token.token_type == TokenType.OPERATOR:
                if token.value == ';':
                    stream.consume()  # Skip the semicolon
                    break
                elif token.value == '&':
                    stream.consume()  # Skip the ampersand
                    background = True
                    break
                elif token.value == '|':
                    # This is handled by the pipeline rule
                    break
                    
            # Check for keywords that might indicate the end of a command
            if token.token_type == TokenType.KEYWORD and token.value in {
                'then', 'else', 'elif', 'fi', 'do', 'done', 'esac'
            }:
                break
                
            # Parse redirections
            if self._is_redirection(token):
                redir = self._parse_redirection(stream, context)
                if redir:
                    redirections.append(redir)
                continue
                
            # If we get here, the token is part of the command
            args.append(stream.consume().value)
            
        # If we hit the token limit, log a warning and break out
        if token_count >= max_tokens:
            import sys
            print("[WARNING] Command parsing exceeded token limit - breaking infinite loop", file=sys.stderr)
            
        # If no arguments were parsed, return None
        if not args:
            # Restore the stream position
            stream.restore_position(start_pos)
            return None
            
        # Create the command node
        command = args[0]
        return CommandNode(command, args, redirections, background)
    
    def _is_redirection(self, token: Token) -> bool:
        """
        Check if a token is a redirection operator.
        
        Args:
            token: The token to check
            
        Returns:
            True if the token is a redirection operator, False otherwise
        """
        if token.token_type != TokenType.OPERATOR:
            return False
            
        return token.value in {'>', '<', '>>', '<<', '>&', '<&', '2>', '2>>'}
    
    def _parse_redirection(self, stream: TokenStream, context: ParserContext) -> Optional[Tuple[str, str]]:
        """
        Parse a redirection from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A tuple of (operator, target) if successful, None otherwise
        """
        # Consume the redirection operator
        op_token = stream.consume()
        op = op_token.value
        
        # Special case for 2>&1
        if op == '2>' and not stream.is_at_end() and stream.peek().value == '&1':
            target_token = stream.consume()
            return ('2>&1', '')
            
        # Check for target
        if stream.is_at_end():
            context.report_error(
                f"Missing target for redirection {op}",
                stream.current_position(),
                "Add a file or descriptor to redirect to"
            )
            return None
            
        # Get the target
        target_token = stream.consume()
        return (op, target_token.value)