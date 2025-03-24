#!/usr/bin/env python3
"""
Context for the state machine expander implementation.
"""

import sys
from typing import List, Optional

from src.parser.state_machine.types import State, TokenType, Token


class StateContext:
    """Context for the state machine"""
    
    def __init__(self, text: str, debug_mode: bool = False):
        self.text = text
        self.pos = 0
        self.tokens: List[Token] = []
        self.current_token_start = 0
        self.current_token_type = TokenType.LITERAL
        self.state_stack: List[State] = [State.NORMAL]
        self.brace_nesting = 0
        self.paren_nesting = 0
        self.debug_mode = debug_mode
    
    @property
    def state(self) -> State:
        """Get the current state"""
        return self.state_stack[-1]
    
    @state.setter
    def state(self, new_state: State):
        """Set the current state"""
        self.state_stack[-1] = new_state
    
    def push_state(self, new_state: State):
        """Push a new state onto the stack"""
        self.state_stack.append(new_state)
    
    def pop_state(self) -> State:
        """Pop and return the current state from the stack"""
        if len(self.state_stack) > 1:
            return self.state_stack.pop()
        return self.state_stack[0]
    
    @property
    def current_char(self) -> str:
        """Get the current character"""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return ''
    
    @property
    def next_char(self) -> str:
        """Get the next character"""
        if self.pos + 1 < len(self.text):
            return self.text[self.pos + 1]
        return ''
    
    def add_token(self, token_type: TokenType, value: Optional[str] = None, raw: Optional[str] = None):
        """Add a token to the list"""
        if value is None:
            # Use the text between current_token_start and current position
            value = self.text[self.current_token_start:self.pos]
        
        if raw is None:
            # Use the same text for raw value
            raw = self.text[self.current_token_start:self.pos]
            
        self.tokens.append(Token(token_type, value, raw))
        # Reset for the next token
        self.current_token_start = self.pos
        self.current_token_type = TokenType.LITERAL
    
    def debug(self, message: str):
        """Print debug information"""
        if self.debug_mode:
            print(f"[DEBUG] {message}", file=sys.stderr)