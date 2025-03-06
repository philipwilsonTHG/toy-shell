#!/usr/bin/env python3
"""
Rule for parsing if statements.
"""

from typing import List, Optional, Set

from .....parser.ast import Node, IfNode, CommandNode, ListNode
from ...token_types import TokenType
from ..grammar_rule import GrammarRule
from ..token_stream import TokenStream
from ..parser_context import ParserContext
from .command_rule import CommandRule


class IfStatementRule(GrammarRule):
    """
    Rule for parsing if statements like "if cmd; then cmd; else cmd; fi".
    
    An if statement consists of a condition, a then branch, an optional else branch,
    and is terminated by 'fi'.
    """
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        Returns:
            A set containing TokenType.KEYWORD, since if statements start with 'if'
        """
        return {TokenType.KEYWORD}
    
    def can_start_with_keyword(self, keyword: str) -> bool:
        """
        Check if this rule can start with the given keyword.
        
        Args:
            keyword: The keyword to check
            
        Returns:
            True if keyword is 'if', False otherwise
        """
        return keyword == 'if'
    
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse an if statement from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            An IfNode representing the if statement, or None if parsing failed
        """
        # Check and consume the 'if' keyword
        if not stream.match_keyword('if'):
            return None
            
        # Parse the condition (commands until 'then')
        condition = self._parse_command_list(stream, context, end_keywords=['then'])
        if condition is None:
            context.report_error(
                "Expected condition after 'if'",
                stream.current_position(),
                "Add a condition after 'if'"
            )
            return None
            
        # Check and consume the 'then' keyword
        if not stream.match_keyword('then'):
            context.report_error(
                "Expected 'then' after if condition",
                stream.current_position(),
                "Add 'then' after the if condition"
            )
            context.mark_in_progress()
            return None
            
        # Parse the 'then' branch (commands until 'else', 'elif', or 'fi')
        then_branch = self._parse_command_list(
            stream, context, end_keywords=['else', 'elif', 'fi'])
        if then_branch is None:
            context.report_error(
                "Expected commands after 'then'",
                stream.current_position(),
                "Add commands after 'then'"
            )
            context.mark_in_progress()
            return None
            
        # Parse the 'else' branch if present
        else_branch = None
        if stream.match_keyword('else'):
            else_branch = self._parse_command_list(stream, context, end_keywords=['fi'])
            if else_branch is None:
                context.report_error(
                    "Expected commands after 'else'",
                    stream.current_position(),
                    "Add commands after 'else'"
                )
                context.mark_in_progress()
                return None
        elif stream.match_keyword('elif'):
            # Recursive parsing of 'elif' as a nested if statement
            else_branch = self.parse(stream, context)
            if else_branch is None:
                context.report_error(
                    "Invalid 'elif' clause",
                    stream.current_position(),
                    "Fix the 'elif' clause syntax"
                )
                context.mark_in_progress()
                return None
                
        # Check and consume the 'fi' keyword
        if not stream.match_keyword('fi'):
            context.report_error(
                "Expected 'fi' to close if statement",
                stream.current_position(),
                "Add 'fi' to close the if statement"
            )
            context.mark_in_progress()
            return None
            
        # Create and return if node
        return IfNode(condition, then_branch, else_branch)
    
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