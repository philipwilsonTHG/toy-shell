#!/usr/bin/env python3
"""
Rule for parsing pipelines of commands.
"""

from typing import List, Optional, Set

from .....parser.ast import Node, CommandNode, PipelineNode
from ...token_types import TokenType
from ..grammar_rule import GrammarRule
from ..token_stream import TokenStream
from ..parser_context import ParserContext
from .command_rule import CommandRule


class PipelineRule(GrammarRule):
    """
    Rule for parsing pipelines like "cmd1 | cmd2 | cmd3".
    
    A pipeline consists of two or more commands separated by pipe operators.
    """
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        Returns:
            The same set as CommandRule, since a pipeline starts with a command
        """
        return CommandRule().can_start_with()
    
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a pipeline from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A PipelineNode representing the pipeline, or None if parsing failed
        """
        # First parse a command
        command_rule = CommandRule()
        first_command = command_rule.parse(stream, context)
        
        if first_command is None:
            return None
            
        # If it's not a command node, we can't make a pipeline
        if not isinstance(first_command, CommandNode):
            return first_command
            
        # Check if this is followed by a pipe
        if stream.is_at_end() or not stream.match_operator('|'):
            return first_command
            
        # Parse the rest of the pipeline
        commands = [first_command]
        
        while not stream.is_at_end():
            # Parse the next command in the pipeline
            next_command = command_rule.parse(stream, context)
            
            if next_command is None:
                context.report_error(
                    "Expected command after pipe",
                    stream.current_position(),
                    "Add a command after the pipe operator"
                )
                break
                
            if not isinstance(next_command, CommandNode):
                context.report_error(
                    "Expected simple command in pipeline",
                    stream.current_position(),
                    "Pipelines must contain simple commands"
                )
                break
                
            commands.append(next_command)
            
            # Check if there are more commands in the pipeline
            if not stream.match_operator('|'):
                break
                
        # Check for background execution
        background = False
        if not stream.is_at_end() and stream.match_operator('&'):
            background = True
            
        # Create pipeline node
        return PipelineNode(commands, background)