#!/usr/bin/env python3
"""
Types used by the state machine expander implementation.
"""

import enum
from typing import Optional


class TokenType(enum.Enum):
    """Token types for the state machine expander"""
    LITERAL = 'LITERAL'         # Regular text
    VARIABLE = 'VARIABLE'       # $VAR
    BRACE_VARIABLE = 'BRACE_VARIABLE'  # ${VAR}
    ARITHMETIC = 'ARITHMETIC'   # $((expr))
    COMMAND = 'COMMAND'         # $(cmd)
    BACKTICK = 'BACKTICK'       # `cmd`
    SINGLE_QUOTED = 'SINGLE_QUOTED'  # 'text'
    DOUBLE_QUOTED = 'DOUBLE_QUOTED'  # "text"
    ESCAPED_CHAR = 'ESCAPED_CHAR'    # \x
    BRACE_PATTERN = 'BRACE_PATTERN'  # {a,b,c}


class Token:
    """Token representation for the state machine expander"""
    
    def __init__(self, token_type: TokenType, value: str, raw: Optional[str] = None):
        self.type = token_type
        self.value = value
        # Raw text is useful for preserving original text when needed
        self.raw = raw if raw is not None else value
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"


class State(enum.Enum):
    """States for the state machine expander"""
    NORMAL = 'NORMAL'             # Regular text
    DOLLAR = 'DOLLAR'             # Just seen $
    VARIABLE = 'VARIABLE'         # Processing variable name
    BRACE_START = 'BRACE_START'   # Just seen ${
    BRACE_VARIABLE = 'BRACE_VARIABLE'  # Inside ${...}
    PAREN_START = 'PAREN_START'   # Just seen $(
    COMMAND = 'COMMAND'           # Inside $(...) - command substitution
    ARITHMETIC_START = 'ARITHMETIC_START'  # Just seen $((
    ARITHMETIC = 'ARITHMETIC'     # Inside $((...))
    BACKTICK = 'BACKTICK'         # Inside `...`
    SINGLE_QUOTE = 'SINGLE_QUOTE'  # Inside '...'
    DOUBLE_QUOTE = 'DOUBLE_QUOTE'  # Inside "..."
    ESCAPE = 'ESCAPE'             # Just seen backslash
    BRACE_PATTERN_START = 'BRACE_PATTERN_START'  # Just seen {
    BRACE_PATTERN = 'BRACE_PATTERN'    # Inside {...}