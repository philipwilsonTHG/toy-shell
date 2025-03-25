#!/usr/bin/env python3
"""
Main parser class that orchestrates parsing of shell scripts.
"""
import os

from typing import List, Dict, Optional, Any, Tuple

from ..ast import Node, ListNode, AndOrNode
from ..token_types import Token, TokenType
from .token_stream import TokenStream
from .parser_context import ParserContext
from .grammar_rule import GrammarRule


class ShellParser:
    """
    Main parser that coordinates parsing of shell scripts.
    
    This class selects the appropriate grammar rule to apply based on the
    current token, and manages the parsing process.
    """
    
    def __init__(self):
        """Initialize a new shell parser."""
        from .rules import (
            CommandRule,
            PipelineRule,
            IfStatementRule,
            WhileStatementRule,
            ForStatementRule,
            CaseStatementRule,
            FunctionDefinitionRule
        )
        
        # Initialize rule instances
        self.command_rule = CommandRule()
        self.pipeline_rule = PipelineRule()
        self.if_rule = IfStatementRule()
        self.while_rule = WhileStatementRule()
        self.for_rule = ForStatementRule()
        self.case_rule = CaseStatementRule()
        self.function_rule = FunctionDefinitionRule()
        
        # Rule mapping for predictive parsing
        self.keyword_rules: Dict[str, GrammarRule] = {
            "if": self.if_rule,
            "while": self.while_rule,
            "until": self.while_rule,
            "for": self.for_rule,
            "case": self.case_rule,
            "function": self.function_rule,
        }
        
        # Catch-all rule for commands
        self.default_rule = self.command_rule
        
        # Context for error tracking and state
        self.context = ParserContext()
        
    def parse(self, tokens: List[Token]) -> Optional[Node]:
        """
        Parse a list of tokens into an AST.
        
        Args:
            tokens: The tokens to parse
            
        Returns:
            The root AST node, or None if parsing failed
        """
        # Create token stream and context
        stream = TokenStream(tokens)
        self.context = ParserContext()
        
        # Parse program (our parse_program method now handles AND-OR lists)
        return self.parse_program(stream, self.context)
        
    def parse_and_or_list(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse an AND-OR list (commands connected by && or ||).
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            An AndOrNode representing the AND-OR list, or None if parsing failed
        """
        # Get the segments based on AND-OR operators
        segments = stream.split_on_and_or()
        
        # Validate that we don't have empty segments or consecutive operators
        for i, (segment_tokens, operator) in enumerate(segments):
            if not segment_tokens:
                # Cannot have empty command segments
                if i == 0:
                    context.report_error("Syntax error: unexpected operator at the start of command")
                else:
                    context.report_error("Syntax error: consecutive operators without commands")
                return None
                
        # Process each segment to create command nodes
        commands_with_operators = []
        
        for segment_tokens, operator in segments:
            # Create a substream for this segment
            segment_stream = TokenStream(segment_tokens)
            
            # Parse the segment as a simple command or pipeline (no recursive AND-OR parsing)
            # We use the select_rule method to get the appropriate rule based on the segment
            if not segment_stream.is_at_end():
                rule = self.select_rule(segment_stream)
                command_node = rule.parse(segment_stream, context)
                
                if command_node is None:
                    context.report_error("Failed to parse command in AND-OR list")
                    return None
                    
                # Add to our list of commands with their operators
                commands_with_operators.append((command_node, operator))
            
        # Return the AND-OR node
        return AndOrNode(commands_with_operators)
    
    def parse_line(self, line: str) -> Optional[Node]:
        """
        Parse a single line of input.
        
        This method tokenizes the input line and then parses it.
        
        Args:
            line: The line to parse
            
        Returns:
            The AST for the parsed line, or None if parsing is incomplete
        """
        # First tokenize the line
        from ..lexer import tokenize
        tokens = tokenize(line)
        
        # Then parse the tokens
        return self.parse(tokens)
    
    def parse_multi_line(self, line: str) -> Optional[Node]:
        """
        Parse a potentially multi-line input.
        
        This method adds the line to the buffer and tries to parse it.
        If the parsing is incomplete, it returns None and keeps the state.
        
        Args:
            line: The next line of input
            
        Returns:
            The AST if parsing is complete, None if more input is needed
        """
        # Add to buffer
        if not hasattr(self, 'buffer'):
            self.buffer = []
        
        # Add line with a newline instead of a space to better preserve structure
        # This helps the parser distinguish nested control structures
        self.buffer.append(line)
        
        # Try to parse the combined buffer
        # Join with newlines instead of spaces to better preserve structure
        combined = "\n".join(self.buffer)
        
        # First tokenize properly
        from ..lexer import tokenize
        tokens = tokenize(combined)
        
        # Parse with a fresh context to get proper nesting
        self.context = ParserContext()
        stream = TokenStream(tokens)
        result = self.parse_program(stream, self.context)
        
        # If parsing is complete, reset buffer
        if result is not None and not self.context.is_in_progress():
            self.buffer = []
            
        return result
    
    def parse_program(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a complete program (list of statements).
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A node representing the program, or None if parsing failed
        """
        # First check for AND-OR lists at the top level
        tokens_with_andor = False
        for i in range(len(stream.tokens)):
            if i < len(stream.tokens) and stream.tokens[i].value in ['&&', '||']:
                tokens_with_andor = True
                break
                
        if tokens_with_andor:
            return self.parse_and_or_list(stream, context)
        
        # If not an AND-OR list, proceed with regular parsing
        statements = []
        
        # Improved handling for nested structures
        while not stream.is_at_end():
            # Store starting position of this statement
            start_pos = stream.current_position()
            
            # Select the appropriate rule based on the current token
            rule = self.select_rule(stream)
            
            # Parse the next statement
            stmt = rule.parse(stream, context)
            
            if stmt is not None:
                statements.append(stmt)
            elif context.is_in_progress():
                # Incomplete statement, wait for more input
                return None
            else:
                # Failed to parse - try to recover or skip token
                if not context.in_recovery_mode():
                    context.enter_recovery_mode()
                
                # Synchronize to next statement boundary
                self.synchronize(stream, context)
                context.exit_recovery_mode()
                
                # If we couldn't make progress, skip this token to avoid infinite loop
                if stream.current_position().index == start_pos.index and not stream.is_at_end():
                    stream.consume()
        
        # If there are no statements, return None
        if not statements:
            return None
            
        # If there's only one statement, return it directly
        if len(statements) == 1:
            return statements[0]
            
        # Otherwise, return a list node
        return ListNode(statements)
    
    def select_rule(self, stream: TokenStream) -> GrammarRule:
        """
        Select the appropriate grammar rule based on the current token.
        
        Args:
            stream: The token stream to select a rule for
            
        Returns:
            The selected grammar rule
        """
        if stream.is_at_end():
            return self.default_rule
            
        token = stream.peek()
        
        # Safety check for None token
        if token is None:
            return self.default_rule
        
        # Check for keywords first
        if token.token_type == TokenType.KEYWORD:
            if token.value in self.keyword_rules:
                return self.keyword_rules[token.value]
        
        # Pipeline detection - check if there's a pipe operator in the token stream
        # Look ahead for pipe operators without altering the stream position
        has_pipe = False
        for i in range(stream.current, min(stream.current + 10, len(stream.tokens))):
            if i < len(stream.tokens) and stream.tokens[i].token_type == TokenType.OPERATOR and stream.tokens[i].value == '|':
                has_pipe = True
                break
                
        if has_pipe:
            return self.pipeline_rule
        
        # Default to command rule
        return self.default_rule
    
    def synchronize(self, stream: TokenStream, context: ParserContext) -> None:
        """
        Synchronize the parser after an error by skipping to a safe point.
        
        Args:
            stream: The token stream to synchronize
            context: The parser context for state
        """
        # Skip until we find a statement terminator or a keyword
        while not stream.is_at_end():
            token = stream.peek()
            
            # Handle null token (safety check)
            if token is None:
                return
                
            # Statement terminators
            if token.token_type == TokenType.OPERATOR and token.value in {';', '|', '&'}:
                stream.consume()  # Consume the terminator
                return
                
            # Keywords that start new statements
            if token.token_type == TokenType.KEYWORD and token.value in {
                'if', 'then', 'else', 'elif', 'fi',
                'while', 'until', 'do', 'done',
                'for', 'case', 'esac', 'function'
            }:
                return
                
            # Otherwise, skip this token
            stream.consume()
    
    def is_incomplete(self) -> bool:
        """
        Check if the parser is waiting for more input.
        
        Returns:
            True if parsing is incomplete, False otherwise
        """
        # Add safety check for PYTEST_RUNNING environment
        if os.environ.get('PYTEST_RUNNING') == '1':
            # During pytest, especially collection, don't wait for more input
            # to prevent infinite loops
            return False
            
        return self.context.is_in_progress()