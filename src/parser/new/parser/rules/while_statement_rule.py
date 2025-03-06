#!/usr/bin/env python3
"""
Rule for parsing while and until statements.
"""

from typing import List, Optional, Set

from .....parser.ast import Node, WhileNode, ListNode
from ...token_types import TokenType
from ..grammar_rule import GrammarRule
from ..token_stream import TokenStream
from ..parser_context import ParserContext
from .command_rule import CommandRule


class WhileStatementRule(GrammarRule):
    """
    Rule for parsing while and until statements like "while cmd; do cmd; done".
    
    A while statement consists of a condition, followed by 'do', a body, and 'done'.
    An until statement is similar but the condition is negated.
    """
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        Returns:
            A set containing TokenType.KEYWORD, since while statements start with 'while' or 'until'
        """
        return {TokenType.KEYWORD}
    
    def can_start_with_keyword(self, keyword: str) -> bool:
        """
        Check if this rule can start with the given keyword.
        
        Args:
            keyword: The keyword to check
            
        Returns:
            True if keyword is 'while' or 'until', False otherwise
        """
        return keyword in {'while', 'until'}
    
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a while or until statement from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A WhileNode representing the while statement, or None if parsing failed
        """
        # Check which type of loop we're parsing
        is_until = False
        if stream.match_keyword('while'):
            is_until = False
        elif stream.match_keyword('until'):
            is_until = True
        else:
            return None
            
        # Parse the condition (commands until 'do')
        condition = self._parse_command_list(stream, context, end_keywords=['do'])
        if condition is None:
            context.report_error(
                f"Expected condition after '{'until' if is_until else 'while'}'",
                stream.current_position(),
                f"Add a condition after '{'until' if is_until else 'while'}'"
            )
            return None
            
        # Check and consume the 'do' keyword
        if not stream.match_keyword('do'):
            context.report_error(
                "Expected 'do' after loop condition",
                stream.current_position(),
                "Add 'do' after the loop condition"
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
                "Expected 'done' to close loop",
                stream.current_position(),
                "Add 'done' to close the loop"
            )
            context.mark_in_progress()
            return None
            
        # Create and return while node
        return WhileNode(condition, body, is_until)
    
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