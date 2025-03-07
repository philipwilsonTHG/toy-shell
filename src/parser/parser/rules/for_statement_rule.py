#!/usr/bin/env python3
"""
Rule for parsing for statements.
"""

from typing import List, Optional, Set

from ...ast import Node, ForNode, ListNode
from ...token_types import TokenType
from ..grammar_rule import GrammarRule
from ..token_stream import TokenStream
from ..parser_context import ParserContext
from .command_rule import CommandRule


class ForStatementRule(GrammarRule):
    """
    Rule for parsing for statements like "for var in a b c; do cmd; done".
    
    A for statement consists of a variable name, a list of values, a body,
    and is terminated by 'done'.
    """
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        Returns:
            A set containing TokenType.KEYWORD, since for statements start with 'for'
        """
        return {TokenType.KEYWORD}
    
    def can_start_with_keyword(self, keyword: str) -> bool:
        """
        Check if this rule can start with the given keyword.
        
        Args:
            keyword: The keyword to check
            
        Returns:
            True if keyword is 'for', False otherwise
        """
        return keyword == 'for'
    
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a for statement from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A ForNode representing the for statement, or None if parsing failed
        """
        # Check and consume the 'for' keyword
        if not stream.match_keyword('for'):
            return None
            
        # Get the variable name
        if stream.is_at_end() or stream.peek().token_type != TokenType.WORD:
            context.report_error(
                "Expected variable name after 'for'",
                stream.current_position(),
                "Add a variable name after 'for'"
            )
            return None
            
        variable = stream.consume().value
        
        # Check and consume the 'in' keyword
        if not stream.match_keyword('in'):
            context.report_error(
                "Expected 'in' after variable name",
                stream.current_position(),
                "Add 'in' after the variable name"
            )
            context.mark_in_progress()
            return None
            
        # Parse the word list (tokens until 'do' or ';')
        words = []
        while not stream.is_at_end():
            # Check if we've reached the end of the word list
            if stream.peek().token_type == TokenType.KEYWORD and stream.peek().value == 'do':
                break
                
            if stream.peek().token_type == TokenType.OPERATOR and stream.peek().value == ';':
                stream.consume()  # Skip the semicolon
                break
                
            # Add the word to the list
            token = stream.consume()
            words.append(token.value)
            
        # Check and consume the 'do' keyword
        if not stream.match_keyword('do'):
            context.report_error(
                "Expected 'do' after word list",
                stream.current_position(),
                "Add 'do' after the word list"
            )
            context.mark_in_progress()
            return None
            
        # Parse the body (commands until 'done')
        body = self._parse_command_list(stream, context, end_keywords=['done'])
        if body is None:
            context.report_error(
                "Expected commands after 'do'",
                stream.current_position(),
                "Add commands after 'do'"
            )
            context.mark_in_progress()
            return None
            
        # Check and consume the 'done' keyword
        if not stream.match_keyword('done'):
            context.report_error(
                "Expected 'done' to close for loop",
                stream.current_position(),
                "Add 'done' to close the for loop"
            )
            context.mark_in_progress()
            return None
            
        # Create and return for node
        return ForNode(variable, words, body)
    
    def _parse_command_list(self, stream: TokenStream, context: ParserContext, 
                           end_keywords: List[str]) -> Optional[Node]:
        """
        Parse a list of commands until one of the end keywords is encountered.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            end_keywords: The keywords that terminate the command list
            
        Returns:
            A Node representing the command list, or None if parsing failed
        """
        # Save the current position
        start_pos = stream.save_position()
        
        # Parse commands until an end keyword is encountered
        commands = []
        command_rule = CommandRule()
        
        # Add safety counter to prevent infinite loops
        max_iterations = len(stream.tokens) * 2  # Generous limit
        iteration_count = 0
        
        while not stream.is_at_end() and iteration_count < max_iterations:
            iteration_count += 1
            
            # Get the current token
            token = stream.peek()
            if token is None:
                # Safety check - sometimes peek can return None in error conditions
                break
                
            # Check if we've reached an end keyword
            if token.token_type == TokenType.KEYWORD and token.value in end_keywords:
                break
                
            # Parse the next command
            command = command_rule.parse(stream, context)
            if command is not None:
                commands.append(command)
            else:
                # If we can't parse a command, skip to the next statement
                token = stream.consume()
                # If we encounter an end keyword, break
                if token.token_type == TokenType.KEYWORD and token.value in end_keywords:
                    # Unconsume the token so it can be processed by the caller
                    stream.restore_position(stream.current_position().index - 1)
                    break
        
        # If we hit the iteration limit, log a warning
        if iteration_count >= max_iterations:
            import sys
            print("[WARNING] Command list parsing exceeded iteration limit - breaking infinite loop", file=sys.stderr)
                    
        # If no commands were parsed, return None
        if not commands:
            # Restore the stream position
            stream.restore_position(start_pos)
            return None
            
        # If there's only one command, return it directly
        if len(commands) == 1:
            return commands[0]
            
        # Otherwise, create a list node
        return ListNode(commands)