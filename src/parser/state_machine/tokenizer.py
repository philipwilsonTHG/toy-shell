#!/usr/bin/env python3
"""
Tokenizer implementation for the state machine expander.
"""

from typing import List, Dict, Callable

from src.parser.state_machine.types import TokenType, Token, State
from src.parser.state_machine.context import StateContext


class Tokenizer:
    """
    State machine based tokenizer for shell expansion.
    Processes text in a single pass, identifying different types of tokens.
    """
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        
        # Define state transition functions
        self.state_handlers = {
            State.NORMAL: self._handle_normal,
            State.DOLLAR: self._handle_dollar,
            State.VARIABLE: self._handle_variable,
            State.BRACE_START: self._handle_brace_start,
            State.BRACE_VARIABLE: self._handle_brace_variable,
            State.PAREN_START: self._handle_paren_start,
            State.COMMAND: self._handle_command,
            State.ARITHMETIC_START: self._handle_arithmetic_start,
            State.ARITHMETIC: self._handle_arithmetic,
            State.BACKTICK: self._handle_backtick,
            State.SINGLE_QUOTE: self._handle_single_quote,
            State.DOUBLE_QUOTE: self._handle_double_quote,
            State.ESCAPE: self._handle_escape,
            State.BRACE_PATTERN_START: self._handle_brace_pattern_start,
            State.BRACE_PATTERN: self._handle_brace_pattern,
        }
    
    def tokenize(self, text: str) -> List[Token]:
        """
        Tokenize the input text into a list of tokens using a state machine approach.
        
        Args:
            text: The input text to tokenize
            
        Returns:
            A list of Token objects
        """
        ctx = StateContext(text, self.debug_mode)
        
        while ctx.pos < len(text):
            # Get the current state handler function
            handler = self.state_handlers.get(ctx.state)
            if handler:
                # Call the handler function
                handler(ctx)
            else:
                # Unknown state - shouldn't happen
                ctx.debug(f"Unknown state: {ctx.state}")
                ctx.pos += 1
            
        # Process any remaining text
        if ctx.pos > ctx.current_token_start:
            ctx.add_token(ctx.current_token_type)
        
        return ctx.tokens
    
    def _handle_normal(self, ctx: StateContext):
        """Handle normal state"""
        char = ctx.current_char
        
        if char == '$':
            # If we have accumulated literal text, add it as a token
            if ctx.pos > ctx.current_token_start:
                ctx.add_token(TokenType.LITERAL)
            
            # Start a new token and transition to DOLLAR state
            ctx.current_token_start = ctx.pos
            ctx.state = State.DOLLAR
            ctx.pos += 1
        
        elif char == '`':
            # If we have accumulated literal text, add it as a token
            if ctx.pos > ctx.current_token_start:
                ctx.add_token(TokenType.LITERAL)
            
            # Start a new token and transition to BACKTICK state
            ctx.current_token_start = ctx.pos
            ctx.state = State.BACKTICK
            ctx.pos += 1
        
        elif char == '\'':
            # If we have accumulated literal text, add it as a token
            if ctx.pos > ctx.current_token_start:
                ctx.add_token(TokenType.LITERAL)
            
            # Start a new token and transition to SINGLE_QUOTE state
            ctx.current_token_start = ctx.pos
            ctx.state = State.SINGLE_QUOTE
            ctx.pos += 1
        
        elif char == '"':
            # If we have accumulated literal text, add it as a token
            if ctx.pos > ctx.current_token_start:
                ctx.add_token(TokenType.LITERAL)
            
            # Start a new token and transition to DOUBLE_QUOTE state
            ctx.current_token_start = ctx.pos
            ctx.state = State.DOUBLE_QUOTE
            ctx.pos += 1
        
        elif char == '\\':
            # If we have accumulated literal text, add it as a token
            if ctx.pos > ctx.current_token_start:
                ctx.add_token(TokenType.LITERAL)
            
            # Start a new token and transition to ESCAPE state
            ctx.current_token_start = ctx.pos
            ctx.state = State.ESCAPE
            ctx.pos += 1
        
        elif char == '{':
            # If we have accumulated literal text, add it as a token
            if ctx.pos > ctx.current_token_start:
                ctx.add_token(TokenType.LITERAL)
            
            # Start a new token and transition to BRACE_PATTERN_START state
            ctx.current_token_start = ctx.pos
            ctx.state = State.BRACE_PATTERN_START
            ctx.pos += 1
        
        else:
            # For all other characters, just accumulate them
            ctx.pos += 1
    
    def _handle_dollar(self, ctx: StateContext):
        """Handle the state right after a dollar sign"""
        char = ctx.current_char
        next_char = ctx.next_char
        
        if char == '{':
            # ${VAR} - transition to BRACE_START
            ctx.state = State.BRACE_START
            ctx.pos += 1
        
        elif char == '(':
            if next_char == '(':
                # $(( - start of arithmetic expression
                ctx.state = State.ARITHMETIC_START
                ctx.pos += 1
            else:
                # $( - start of command substitution
                ctx.state = State.PAREN_START
                ctx.pos += 1
        
        elif char.isalpha() or char == '_':
            # $VAR - start of variable
            ctx.current_token_type = TokenType.VARIABLE
            ctx.state = State.VARIABLE
            ctx.pos += 1
        
        elif char in '*@#?$!-':
            # Special shell variables $*, $@, $#, $?, $$, $!, $-
            ctx.add_token(TokenType.VARIABLE, f"${char}")
            ctx.pos += 1
            ctx.state = State.NORMAL
        
        elif char.isdigit():
            # Positional parameter $0, $1, etc.
            ctx.add_token(TokenType.VARIABLE, f"${char}")
            ctx.pos += 1
            ctx.state = State.NORMAL
        
        else:
            # Just a dollar sign, not a variable
            ctx.add_token(TokenType.LITERAL, "$")
            ctx.state = State.NORMAL
    
    def _handle_variable(self, ctx: StateContext):
        """Handle variable name after $"""
        char = ctx.current_char
        
        if char.isalnum() or char == '_':
            # Continue accumulating the variable name
            ctx.pos += 1
        else:
            # End of variable name
            ctx.add_token(TokenType.VARIABLE)
            ctx.state = State.NORMAL
    
    def _handle_brace_start(self, ctx: StateContext):
        """Handle the state right after ${ - start of brace expansion"""
        ctx.state = State.BRACE_VARIABLE
        ctx.brace_nesting = 1
        # Already moved past the { character
    
    def _handle_brace_variable(self, ctx: StateContext):
        """Handle the content inside ${...}"""
        char = ctx.current_char
        
        if char == '}':
            ctx.brace_nesting -= 1
            if ctx.brace_nesting == 0:
                # End of brace variable
                ctx.pos += 1  # Include the closing brace
                ctx.add_token(TokenType.BRACE_VARIABLE)
                ctx.state = State.NORMAL
            else:
                ctx.pos += 1
        elif char == '{':
            ctx.brace_nesting += 1
            ctx.pos += 1
        else:
            ctx.pos += 1
    
    def _handle_paren_start(self, ctx: StateContext):
        """Handle the state right after $( - start of command substitution"""
        ctx.state = State.COMMAND
        ctx.paren_nesting = 1
        # Already moved past the ( character
    
    def _handle_command(self, ctx: StateContext):
        """Handle the content inside $(...) - command substitution"""
        char = ctx.current_char
        
        if char == ')':
            ctx.paren_nesting -= 1
            if ctx.paren_nesting == 0:
                # End of command substitution
                ctx.pos += 1  # Include the closing parenthesis
                ctx.add_token(TokenType.COMMAND)
                ctx.state = State.NORMAL
            else:
                ctx.pos += 1
        elif char == '(':
            ctx.paren_nesting += 1
            ctx.pos += 1
        else:
            ctx.pos += 1
    
    def _handle_arithmetic_start(self, ctx: StateContext):
        """Handle the state right after $(( - start of arithmetic expression"""
        # Move to the actual arithmetic expression
        ctx.pos += 1  # Skip the second (
        ctx.state = State.ARITHMETIC
        ctx.paren_nesting = 2  # We've already seen 2 opening parentheses
    
    def _handle_arithmetic(self, ctx: StateContext):
        """Handle the content inside $((...)) - arithmetic expression"""
        char = ctx.current_char
        next_char = ctx.next_char
        
        if char == ')' and next_char == ')':
            ctx.paren_nesting -= 2
            if ctx.paren_nesting == 0:
                # End of arithmetic expression
                ctx.pos += 2  # Skip both closing parentheses
                ctx.add_token(TokenType.ARITHMETIC)
                ctx.state = State.NORMAL
            else:
                ctx.pos += 2
        elif char == '(':
            ctx.paren_nesting += 1
            ctx.pos += 1
        elif char == ')':
            ctx.paren_nesting -= 1
            ctx.pos += 1
        else:
            ctx.pos += 1
    
    def _handle_backtick(self, ctx: StateContext):
        """Handle content inside backticks - command substitution"""
        char = ctx.current_char
        
        if char == '`':
            # End of backtick command
            ctx.pos += 1  # Include the closing backtick
            ctx.add_token(TokenType.BACKTICK)
            ctx.state = State.NORMAL
        elif char == '\\':
            # Backslash escaping within backticks
            if ctx.next_char in ('`', '\\', '$'):
                # Skip the backslash but include the escaped character
                ctx.pos += 2
            else:
                # Keep the backslash for other characters
                ctx.pos += 1
        else:
            ctx.pos += 1
    
    def _handle_single_quote(self, ctx: StateContext):
        """Handle content inside single quotes"""
        char = ctx.current_char
        
        if char == '\'':
            # End of single quote - no expansions in single quotes
            ctx.pos += 1  # Include the closing quote
            ctx.add_token(TokenType.SINGLE_QUOTED)
            ctx.state = State.NORMAL
        else:
            ctx.pos += 1
    
    def _handle_double_quote(self, ctx: StateContext):
        """Handle content inside double quotes"""
        char = ctx.current_char
        
        if char == '"':
            # End of double quote
            ctx.pos += 1  # Include the closing quote
            ctx.add_token(TokenType.DOUBLE_QUOTED)
            ctx.state = State.NORMAL
        elif char == '\\':
            # Backslash escaping within double quotes
            if ctx.next_char in ('"', '\\', '$', '`'):
                # Skip the backslash but include the escaped character
                ctx.pos += 2
            else:
                # Keep the backslash for other characters
                ctx.pos += 1
        elif char == '$':
            # Handle variable expansion inside double quotes
            # Save the current double-quoted content up to this point
            if ctx.pos > ctx.current_token_start:
                double_quote_text = ctx.text[ctx.current_token_start:ctx.pos]
                ctx.add_token(TokenType.DOUBLE_QUOTED, double_quote_text)
            
            # Start a new token for the variable and transition to DOLLAR state
            ctx.current_token_start = ctx.pos
            ctx.state = State.DOLLAR
            ctx.pos += 1
        elif char == '`':
            # Handle command substitution inside double quotes
            # Save the current double-quoted content up to this point
            if ctx.pos > ctx.current_token_start:
                double_quote_text = ctx.text[ctx.current_token_start:ctx.pos]
                ctx.add_token(TokenType.DOUBLE_QUOTED, double_quote_text)
            
            # Start a new token for the backtick and transition to BACKTICK state
            ctx.current_token_start = ctx.pos
            ctx.state = State.BACKTICK
            ctx.pos += 1
        else:
            ctx.pos += 1
    
    def _handle_escape(self, ctx: StateContext):
        """Handle escape sequences"""
        if ctx.pos < len(ctx.text) - 1:  # Ensure there's at least one character after the backslash
            next_char = ctx.next_char
            
            # Special handling for escaped $ - convert to variable token
            if next_char == '$':
                # Skip the backslash
                ctx.pos += 1
                
                # If we have accumulated literal text, add it as a token
                if ctx.pos > ctx.current_token_start + 1:  # +1 because we skipped the backslash
                    pre_text = ctx.text[ctx.current_token_start:ctx.pos-1]
                    ctx.add_token(TokenType.LITERAL, pre_text)
                
                # Start a new token at the $ position
                ctx.current_token_start = ctx.pos
                ctx.state = State.DOLLAR
                return
                
            # Normal escaped character handling
            escaped_char = ctx.text[ctx.pos:ctx.pos+2]  # Get backslash and escaped character
            ctx.add_token(TokenType.ESCAPED_CHAR, escaped_char)
            ctx.pos += 2  # Skip both the backslash and the escaped character
        else:
            # Trailing backslash at end of input
            ctx.add_token(TokenType.ESCAPED_CHAR, "\\")
            ctx.pos += 1
        ctx.state = State.NORMAL
    
    def _handle_brace_pattern_start(self, ctx: StateContext):
        """Handle the state right after { - start of brace pattern"""
        ctx.state = State.BRACE_PATTERN
        ctx.brace_nesting = 1
        # Already moved past the { character
    
    def _handle_brace_pattern(self, ctx: StateContext):
        """Handle the content inside {...} - brace pattern"""
        char = ctx.current_char
        
        if char == '}':
            ctx.brace_nesting -= 1
            if ctx.brace_nesting == 0:
                # End of brace pattern
                ctx.pos += 1  # Include the closing brace
                ctx.add_token(TokenType.BRACE_PATTERN)
                ctx.state = State.NORMAL
            else:
                ctx.pos += 1
        elif char == '{':
            ctx.brace_nesting += 1
            ctx.pos += 1
        else:
            ctx.pos += 1