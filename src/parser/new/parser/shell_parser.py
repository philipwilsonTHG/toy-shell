#!/usr/bin/env python3
"""
Main parser class that orchestrates parsing of shell scripts.
"""

from typing import List, Dict, Optional, Any

from ....parser.ast import Node, ListNode
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
        context = ParserContext()
        
        # Parse program
        return self.parse_program(stream, context)
    
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
        
        self.buffer.append(line)
        
        # Try to parse the combined buffer
        combined = " ".join(self.buffer)
        result = self.parse_line(combined)
        
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
        statements = []
        
        while not stream.is_at_end():
            # Select the appropriate rule based on the current token
            rule = self.select_rule(stream)
            
            # Parse the next statement
            stmt = rule.parse(stream, context)
            if stmt is not None:
                statements.append(stmt)
            
            # If we're in recovery mode, skip to the next statement
            if context.in_recovery_mode():
                self.synchronize(stream, context)
                context.exit_recovery_mode()
        
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
        
        # Check for keywords first
        if token.token_type == TokenType.KEYWORD:
            if token.value in self.keyword_rules:
                return self.keyword_rules[token.value]
        
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
        return self.context.is_in_progress()