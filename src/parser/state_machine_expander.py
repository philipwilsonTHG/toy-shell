#!/usr/bin/env python3
"""
State Machine based implementation for shell variable expansion.
Provides a more efficient tokenizer and expander using state machine approach.
"""

import sys
import re
import enum
import subprocess
from typing import List, Dict, Optional, Callable


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


class StateMachineExpander:
    """
    State machine based expander for shell expansions.
    Uses the Tokenizer to break input into tokens, then expands each token.
    """
    
    def __init__(self, scope_provider: Callable[[str], Optional[str]], debug_mode: bool = False):
        """
        Initialize the expander
        
        Args:
            scope_provider: A function that resolves variable names to values
            debug_mode: Whether to print debug information
        """
        self.scope_provider = scope_provider
        self.debug_mode = debug_mode
        self.tokenizer = Tokenizer(debug_mode)
        
        # Cache for variable lookups and expression evaluations
        self.var_cache: Dict[str, str] = {}
        self.expr_cache: Dict[str, str] = {}
    
    def expand(self, text: str) -> str:
        """
        Expand all shell constructs in the input text
        
        Args:
            text: The input text to expand
            
        Returns:
            The expanded text
        """
        # Fast path for empty or simple strings
        if not text or not any(c in text for c in ('$', '{', '`', '\\', '\'', '"')):
            return text
            
        # Special handling for quoted strings
        if text.startswith('"') and text.endswith('"') and len(text) >= 2:
            # For double-quoted strings, expand the content without the quotes
            content = text[1:-1]
            expanded = self.expand_unquoted(content)
            return expanded
        elif text.startswith("'") and text.endswith("'") and len(text) >= 2:
            # For single-quoted strings, return content without expansion
            return text[1:-1]
            
        # For unquoted text
        return self.expand_unquoted(text)
    
    def expand_unquoted(self, text: str) -> str:
        """Expand unquoted text with all expansions"""
        # Handle escaped characters specially
        if '\\' in text:
            # Process escaped characters correctly
            text = self._preprocess_escapes(text)
        
        # Tokenize the input
        tokens = self.tokenizer.tokenize(text)
        
        # Expand each token
        expanded_parts = []
        for token in tokens:
            expanded = self._expand_token(token)
            expanded_parts.append(expanded)
        
        # Join the expanded parts
        return ''.join(expanded_parts)
        
    def _preprocess_escapes(self, text: str) -> str:
        """Pre-process escaped characters before tokenization"""
        result = ""
        i = 0
        while i < len(text):
            if text[i] == '\\' and i < len(text) - 1:
                # Process special escape sequences
                if text[i+1] == '$':
                    result += 'ESC_DOLLAR'  # Special marker
                    i += 2
                elif text[i+1] == '\\':
                    result += 'ESC_BACKSLASH'  # Special marker
                    i += 2
                else:
                    # Keep other escape sequences
                    result += text[i:i+2]
                    i += 2
            else:
                result += text[i]
                i += 1
                
        # Replace special markers back after tokenization
        result = result.replace('ESC_DOLLAR', '$')
        result = result.replace('ESC_BACKSLASH', '\\')
        return result
    
    def _expand_token(self, token: Token) -> str:
        """Expand a single token"""
        if token.type == TokenType.LITERAL:
            return token.value
        
        elif token.type == TokenType.VARIABLE:
            return self._expand_variable(token.value)
        
        elif token.type == TokenType.BRACE_VARIABLE:
            return self._expand_brace_variable(token.value)
        
        elif token.type == TokenType.ARITHMETIC:
            return self._expand_arithmetic(token.value)
        
        elif token.type == TokenType.COMMAND:
            return self._expand_command(token.value)
        
        elif token.type == TokenType.BACKTICK:
            return self._expand_backtick(token.value)
        
        elif token.type == TokenType.SINGLE_QUOTED:
            # Remove the quotes and return the content without expansion
            return token.value[1:-1] if len(token.value) >= 2 else token.value
        
        elif token.type == TokenType.DOUBLE_QUOTED:
            # Remove the quotes and expand the content
            content = token.value[1:-1] if len(token.value) >= 2 else token.value
            # Recursively expand the content
            expanded = self.expand_unquoted(content)
            return expanded
        
        elif token.type == TokenType.ESCAPED_CHAR:
            # Just return the escaped character (without the backslash)
            if len(token.value) >= 2:
                if token.value.startswith('\\$'):
                    return '$'
                elif token.value.startswith('\\\\'):
                    return '\\'
                else:
                    return token.value[1:]
            return token.value
        
        elif token.type == TokenType.BRACE_PATTERN:
            return self._expand_brace_pattern(token.value)
        
        # Unknown token type
        return token.value
    
    def _expand_variable(self, var_text: str) -> str:
        """Expand a variable token like $VAR"""
        # Check if it's actually a variable pattern
        if not var_text.startswith('$'):
            return var_text
        
        # Extract the variable name
        var_name = var_text[1:]
        
        # Check the cache
        if var_name in self.var_cache:
            return self.var_cache[var_name]
        
        # Get the variable value from the scope provider
        value = self.scope_provider(var_name)
        
        # Cache the result
        result = value or ''
        self.var_cache[var_name] = result
        
        if self.debug_mode:
            print(f"[DEBUG] Expanded {var_text} to '{value}'", file=sys.stderr)
        
        return result
    
    def _expand_brace_variable(self, brace_text: str) -> str:
        """Expand a brace variable token like ${VAR}"""
        # Check if it's actually a brace variable pattern
        if not (brace_text.startswith('${') and brace_text.endswith('}')):
            return brace_text
        
        # Extract the variable name and modifiers
        var_content = brace_text[2:-1]
        
        # Check for modifiers
        if ':' in var_content:
            # Handle modifiers like ${VAR:-default}
            return self._expand_variable_with_modifier(var_content)
        
        # Simple variable reference
        var_name = var_content
        
        # Check the cache
        if var_name in self.var_cache:
            return self.var_cache[var_name]
        
        # Get the variable value from the scope provider
        value = self.scope_provider(var_name)
        
        # Cache the result
        result = value or ''
        self.var_cache[var_name] = result
        
        if self.debug_mode:
            print(f"[DEBUG] Expanded {brace_text} to '{value}'", file=sys.stderr)
        
        return result
    
    def _expand_variable_with_modifier(self, var_content: str) -> str:
        """Expand a variable with modifiers like ${VAR:-default}"""
        # Split into variable name and modifier
        parts = var_content.split(':', 1)
        var_name = parts[0]
        modifier = parts[1] if len(parts) > 1 else ''
        
        # Get the variable value
        value = self.scope_provider(var_name)
        
        # Apply modifiers
        if not modifier:
            return value or ''
        
        # Handle different modifier types
        if modifier.startswith('-'):
            # ${VAR:-default} - use default if VAR is unset or empty
            default_value = modifier[1:]
            # Recursively expand the default value since it may contain variables
            if not value:
                return self.expand(default_value)
            return value
        
        elif modifier.startswith('='):
            # ${VAR:=default} - set VAR to default if unset or empty
            default_value = modifier[1:]
            if not value:
                # This would normally set the variable, but we're just returning the value
                expanded_default = self.expand(default_value)
                self.var_cache[var_name] = expanded_default  # Simulate setting the variable
                return expanded_default
            return value
        
        elif modifier.startswith('?'):
            # ${VAR:?error} - display error if VAR is unset or empty
            error_msg = modifier[1:] or f"{var_name}: parameter null or not set"
            if not value:
                error_expanded = self.expand(error_msg)
                print(f"Error: {error_expanded}", file=sys.stderr)
                return ''
            return value
        
        elif modifier.startswith('+'):
            # ${VAR:+alternate} - use alternate if VAR is set and not empty
            alternate = modifier[1:]
            if value:
                return self.expand(alternate)
            return ''
        
        # Handle substring extraction ${VAR:offset:length}
        if re.match(r'^\d+', modifier):
            parts = modifier.split(':', 1)
            try:
                offset = int(parts[0])
                if len(parts) > 1 and parts[1]:
                    length = int(parts[1])
                    return value[offset:offset+length] if value else ''
                else:
                    return value[offset:] if value else ''
            except (ValueError, IndexError):
                return ''
        
        # Unknown modifier
        return value or ''
    
    def _expand_arithmetic(self, arith_text: str) -> str:
        """Expand an arithmetic expression token like $((expr))"""
        # Check if it's actually an arithmetic expression
        if not (arith_text.startswith('$((') and arith_text.endswith('))')):
            return arith_text
        
        # Extract the expression
        expression = arith_text[3:-2]
        
        # Check the cache
        if expression in self.expr_cache:
            return self.expr_cache[expression]
        
        # Create a dictionary of variables for evaluation
        variables = {}
        
        # Extract variable names from the expression
        var_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)')
        var_names = var_pattern.findall(expression)
        
        # Resolve each variable
        for var_name in var_names:
            var_value = self.scope_provider(var_name)
            if var_value is None:
                variables[var_name] = 0  # Default to 0 for undefined variables
            else:
                try:
                    # Try to convert to number
                    variables[var_name] = int(var_value)
                except ValueError:
                    variables[var_name] = 0  # Default to 0 for non-numeric values
        
        try:
            # Evaluate the expression in a safe environment
            result = eval(expression, {"__builtins__": {}}, variables)
            
            # Cache the result
            result_str = str(result)
            self.expr_cache[expression] = result_str
            
            if self.debug_mode:
                print(f"[DEBUG] Evaluated arithmetic expression: '{expression}' -> {result}", file=sys.stderr)
            
            return result_str
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Error evaluating arithmetic expression: '{expression}': {e}", file=sys.stderr)
            return "0"  # Default to 0 on error
    
    def _expand_command(self, cmd_text: str) -> str:
        """Expand a command substitution token like $(cmd)"""
        # Check if it's actually a command substitution
        if not (cmd_text.startswith('$(') and cmd_text.endswith(')')):
            return cmd_text
        
        # Extract the command
        command = cmd_text[2:-1]
        
        try:
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            output = result.stdout.rstrip('\n')
            
            if self.debug_mode:
                print(f"[DEBUG] Command substitution: '{command}' -> '{output}'", file=sys.stderr)
            
            return output
        except subprocess.SubprocessError as e:
            if self.debug_mode:
                print(f"[DEBUG] Error in command substitution: '{command}': {e}", file=sys.stderr)
            return ""
    
    def _expand_backtick(self, backtick_text: str) -> str:
        """Expand a backtick command substitution token like `cmd`"""
        # Check if it's actually a backtick substitution
        if not (backtick_text.startswith('`') and backtick_text.endswith('`')):
            return backtick_text
        
        # Extract the command
        command = backtick_text[1:-1]
        
        try:
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            output = result.stdout.rstrip('\n')
            
            if self.debug_mode:
                print(f"[DEBUG] Backtick substitution: '{command}' -> '{output}'", file=sys.stderr)
            
            return output
        except subprocess.SubprocessError as e:
            if self.debug_mode:
                print(f"[DEBUG] Error in backtick substitution: '{command}': {e}", file=sys.stderr)
            return ""
    
    def _expand_brace_pattern(self, brace_text: str) -> str:
        """Expand a brace pattern token like {a,b,c}"""
        # Check if it's actually a brace pattern
        if not (brace_text.startswith('{') and brace_text.endswith('}')):
            return brace_text
        
        # Extract the pattern
        pattern = brace_text[1:-1]
        
        # Check for range pattern like {1..5}
        range_match = re.match(r'([^.]+)\.\.([^.]+)', pattern)
        if range_match and ',' not in pattern:
            start, end = range_match.groups()
            
            # Generate the range
            if start.isdigit() and end.isdigit():
                # Numeric range
                start_val, end_val = int(start), int(end)
                step = 1 if start_val <= end_val else -1
                items = [str(i) for i in range(start_val, end_val + step, step)]
                return ' '.join(items)
            
            elif len(start) == 1 and len(end) == 1 and start.isalpha() and end.isalpha():
                # Alphabetic range
                start_val, end_val = ord(start), ord(end)
                step = 1 if start_val <= end_val else -1
                items = [chr(i) for i in range(start_val, end_val + step, step)]
                return ' '.join(items)
            
            # Not a valid range
            return brace_text
        
        # Handle comma-separated list
        if ',' in pattern:
            # Split by commas, respecting nested braces
            items = self._split_brace_pattern(pattern)
            return ' '.join(items)
        
        # Not a valid pattern
        return brace_text
    
    def _split_brace_pattern(self, pattern: str) -> List[str]:
        """Split a brace pattern by commas, respecting nested braces"""
        items = []
        item_start = 0
        brace_level = 0
        
        for i, char in enumerate(pattern):
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1
            elif char == ',' and brace_level == 0:
                # Found a comma at the top level
                items.append(pattern[item_start:i])
                item_start = i + 1
        
        # Add the last item
        items.append(pattern[item_start:])
        
        return items
    
    def clear_caches(self):
        """Clear all caches"""
        self.var_cache.clear()
        self.expr_cache.clear()