#!/usr/bin/env python3
"""
Rule for parsing function definitions.
"""

from typing import Optional, Set

from ...ast import Node, FunctionNode, ListNode
from ...token_types import TokenType
from ..grammar_rule import GrammarRule
from ..token_stream import TokenStream
from ..parser_context import ParserContext
from .command_rule import CommandRule


class FunctionDefinitionRule(GrammarRule):
    """
    Rule for parsing function definitions like "function name() { cmd; }".
    
    A function definition consists of the 'function' keyword, a name,
    optional parentheses, and a body that may be a compound statement or a simple command.
    """
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        Returns:
            A set containing TokenType.KEYWORD, since function definitions start with 'function'
        """
        return {TokenType.KEYWORD}
    
    def can_start_with_keyword(self, keyword: str) -> bool:
        """
        Check if this rule can start with the given keyword.
        
        Args:
            keyword: The keyword to check
            
        Returns:
            True if keyword is 'function', False otherwise
        """
        return keyword == 'function'
    
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a function definition from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A FunctionNode representing the function definition, or None if parsing failed
        """
        # Check and consume the 'function' keyword
        if not stream.match_keyword('function'):
            return None
            
        # Get the function name
        if stream.is_at_end() or stream.peek().token_type != TokenType.WORD:
            context.report_error(
                "Expected function name after 'function'",
                stream.current_position(),
                "Add a function name after 'function'"
            )
            return None
            
        name = stream.consume().value
        
        # Check for optional parentheses
        if not stream.is_at_end() and stream.peek().token_type == TokenType.OPERATOR:
            if stream.match_operator('('):
                # Check for closing parenthesis
                if not stream.match_operator(')'):
                    context.report_error(
                        "Expected ')' after '(' in function definition",
                        stream.current_position(),
                        "Add ')' after '(' in the function definition"
                    )
                    return None
                    
        # Parse the function body
        # First, check for a compound statement enclosed in {}
        if not stream.is_at_end() and stream.peek().token_type == TokenType.OPERATOR and stream.peek().value == '{':
            # Parse a compound statement
            body = self._parse_compound_statement(stream, context)
        else:
            # Check if the next token might be the start of a block on the next line
            if stream.is_at_end() or stream.peek().token_type != TokenType.WORD:
                # Assume this might be a multi-line function with the opening brace on the next line
                context.mark_in_progress()
                return None
                
            # Parse a simple command
            command_rule = CommandRule()
            body = command_rule.parse(stream, context)
            
        if body is None:
            context.report_error(
                "Expected function body",
                stream.current_position(),
                "Add a body for the function definition"
            )
            return None
            
        # Create and return function node
        return FunctionNode(name, body)
    
    def _parse_compound_statement(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a compound statement enclosed in curly braces.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A Node representing the compound statement, or None if parsing failed
        """
        # Check and consume the opening brace - return early if missing
        if not stream.match_operator('{'):
            return None
            
        # Parse commands until closing brace
        commands = []
        command_rule = CommandRule()
        
        # Initialize a brace counter to handle nested braces
        brace_depth = 1  # We've already consumed one opening brace
        
        while not stream.is_at_end():
            # Check if we've reached the closing brace at the correct nesting level
            if stream.peek().token_type == TokenType.OPERATOR:
                if stream.peek().value == '{':
                    # Found another opening brace - increment depth counter
                    brace_depth += 1
                    # Don't consume it, let the command parser handle it
                elif stream.peek().value == '}':
                    # Found closing brace - decrement depth counter
                    brace_depth -= 1
                    
                    # If we've found the matching closing brace for our function body
                    if brace_depth == 0:
                        # Consume the closing brace and break out of the loop
                        stream.consume()
                        break
            
            # Parse the next command
            command = command_rule.parse(stream, context)
            if command is not None:
                commands.append(command)
            else:
                # If we can't parse a command but haven't reached the end, consume one token
                # to avoid an infinite loop, but be careful not to consume our closing brace
                if not stream.is_at_end() and not (stream.peek().token_type == TokenType.OPERATOR and 
                                                  stream.peek().value == '}' and brace_depth == 1):
                    stream.consume()
                elif stream.peek().token_type == TokenType.OPERATOR and stream.peek().value == '}':
                    # We found a closing brace we need, but let the brace counter handle it
                    # in the next iteration, don't consume it here
                    pass
                else:
                    # If we're at the end or have an unexpected token, just break
                    break
            
        # Check if we've consumed all braces properly
        if brace_depth > 0:
            context.report_error(
                f"Expected '{brace_depth}' more closing braces '}}' to complete function body",
                stream.current_position(),
                "Add missing closing braces to complete the function body"
            )
            return None
            
        # If no commands were parsed, create an empty command list so function still works
        if not commands:
            # Return an empty list node rather than None for empty function bodies
            return ListNode([])
            
        # If there's only one command, return it directly
        if len(commands) == 1:
            return commands[0]
            
        # Otherwise, create a list node
        return ListNode(commands)