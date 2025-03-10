#!/usr/bin/env python3

from typing import List, Tuple, Dict, Optional, Set
import re
import sys

from .token_types import Token, TokenType, KEYWORDS, create_word_token, create_operator_token, create_substitution_token, create_arithmetic_token

class Lexer:
    """Shell script lexer that handles tokenization with proper context tracking"""
    
    def __init__(self):
        # State tracking for the lexer
        self.reset()
        
        # Recognized shell operators
        self.operators = {'|', '>', '<', '&', ';', '[', ']', '(', ')'}
        # Note: { and } are handled specially for brace expansion
        
        # Multi-character operators
        self.multi_char_operators = {
            '&&', '||',  # Logical operators
            '>>', '<<',  # Redirection operators
            '>&', '<&',  # File descriptor redirection
            '|&',        # Pipeline with stderr
            '2>', '2>>'  # Stderr redirection
        }
        
        # Operator detection pattern (removed { and } for brace expansion handling)
        self.operator_pattern = re.compile(r'[|><&;\[\]()\\\'"$]')
    
    def reset(self):
        """Reset lexer state"""
        self.in_single_quote = False
        self.in_double_quote = False
        self.escaped = False
        self.buffer = []
        self.tokens = []
    
    def tokenize(self, line: str) -> List[Token]:
        """Tokenize a command line with proper handling of quotes, substitutions, etc."""
        self.reset()
        
        i = 0
        while i < len(line):
            char = line[i]
            
            # Handle comments
            if char == '#' and not self.in_quotes():
                break
            
            # Handle escape sequences
            if self.escaped:
                i = self.handle_escaped_char(line, i)
                continue
                
            if char == '\\':
                self.escaped = True
                i += 1
                continue
            
            # Handle quotes
            if self.in_single_quote:
                i = self.handle_single_quoted(line, i)
                continue
                
            if self.in_double_quote:
                i = self.handle_double_quoted(line, i)
                continue
                
            if char in ("'", '"'):
                i = self.handle_quote_start(line, i)
                continue
            
            # Handle special characters
            if char == '$':
                i = self.handle_variable_or_substitution(line, i)
                continue
                
            if char == '`':
                i = self.handle_backtick_substitution(line, i)
                continue
            
            # Handle stderr redirection (2>)
            if char == '2' and i + 1 < len(line) and line[i + 1] in {'>', '<'}:
                i = self.handle_stderr_redirection(line, i)
                continue
            
            # Handle brace expansion patterns
            if char == '{' and not self.in_quotes():
                i = self.handle_brace_expansion(line, i)
                continue
                
            # Handle closing brace (if not part of a brace expansion pattern)
            if char == '}' and not self.in_quotes():
                i = self.handle_operator(line, i)
                continue
                
            # Handle operators
            if char in self.operators:
                i = self.handle_operator(line, i)
                continue
            
            # Handle whitespace
            if char.isspace():
                i = self.finish_current_token(i)
                i += 1
                continue
            
            # Normal character - add to buffer
            self.buffer.append(char)
            i += 1
        
        # Handle any remaining characters in buffer
        self.finish_current_token(len(line))
        
        # Validate quotes
        if self.in_single_quote:
            raise ValueError("Unterminated single quote")
        if self.in_double_quote:
            raise ValueError("Unterminated double quote")
        
        # Mark keywords
        self.identify_keywords()
        
        return self.tokens
    
    def in_quotes(self) -> bool:
        """Check if currently within quotes"""
        return self.in_single_quote or self.in_double_quote
    
    def handle_escaped_char(self, line: str, i: int) -> int:
        """Handle an escaped character"""
        char = line[i]
        # Add both the backslash and the character to preserve escaping
        self.buffer.append('\\')
        self.buffer.append(char)
        self.escaped = False
        return i + 1
    
    def handle_single_quoted(self, line: str, i: int) -> int:
        """Handle character inside single quotes"""
        char = line[i]
        
        if char == "'":
            # End of single-quoted string
            self.buffer.append(char)
            token = create_word_token(''.join(self.buffer), quoted=True)
            self.tokens.append(token)
            self.buffer = []
            self.in_single_quote = False
        else:
            # Add character as-is inside single quotes
            self.buffer.append(char)
            
        return i + 1
    
    def handle_double_quoted(self, line: str, i: int) -> int:
        """Handle character inside double quotes"""
        char = line[i]
        
        if char == '"':
            # End of double-quoted string
            self.buffer.append(char)
            token = create_word_token(''.join(self.buffer), quoted=True)
            self.tokens.append(token)
            self.buffer = []
            self.in_double_quote = False
        else:
            # Add character as-is inside double quotes
            self.buffer.append(char)
            
        return i + 1
    
    def handle_quote_start(self, line: str, i: int) -> int:
        """Handle start of a quoted string"""
        char = line[i]
        
        # If we have content in the buffer, add it as a token first
        if self.buffer:
            self.tokens.append(create_word_token(''.join(self.buffer)))
            self.buffer = []
        
        # Start a new quoted string
        self.buffer.append(char)
        if char == "'":
            self.in_single_quote = True
        else:  # char == '"'
            self.in_double_quote = True
            
        return i + 1
    
    def handle_variable_or_substitution(self, line: str, i: int) -> int:
        """Handle $ (variable, command substitution, or arithmetic expansion)"""
        # If we're in single quotes, treat as literal
        if self.in_single_quote:
            self.buffer.append('$')
            return i + 1
        
        # Check for $(( expression )) arithmetic expansion
        if i + 2 < len(line) and line[i + 1] == '(' and line[i + 2] == '(':
            if self.buffer:
                self.tokens.append(create_word_token(''.join(self.buffer)))
                self.buffer = []
            
            # Extract the expression inside $(( ))
            expr_start = i + 3
            expr_end = expr_start
            paren_count = 2  # Start with 2 for the double parentheses
            sub_escaped = False
            
            while expr_end < len(line) and paren_count > 0:
                if sub_escaped:
                    sub_escaped = False
                    expr_end += 1
                    continue
                
                if line[expr_end] == '(' and not sub_escaped:
                    paren_count += 1
                elif line[expr_end] == ')' and not sub_escaped:
                    paren_count -= 1
                elif line[expr_end] == '\\':
                    sub_escaped = True
                
                expr_end += 1
                
                if expr_end >= len(line) and paren_count > 0:
                    raise ValueError("Unterminated arithmetic expansion")
            
            expr_end -= 1  # adjust for the last increment
            
            # Check if we ended with double parenthesis
            if expr_end >= 1 and line[expr_end] == ')' and line[expr_end - 1] == ')':
                # Create an arithmetic token with the entire $(( )) expression
                self.tokens.append(create_arithmetic_token(line[i:expr_end + 1]))
                return expr_end + 1
            else:
                raise ValueError("Malformed arithmetic expansion, expected double parenthesis '$(( expr ))'")
            
        # Check for $() command substitution
        elif i + 1 < len(line) and line[i + 1] == '(':
            if self.buffer:
                self.tokens.append(create_word_token(''.join(self.buffer)))
                self.buffer = []
            
            # Extract the command inside $()
            cmd_start = i + 2
            cmd_end = cmd_start
            paren_count = 1
            sub_escaped = False
            
            while cmd_end < len(line) and paren_count > 0:
                if sub_escaped:
                    sub_escaped = False
                    cmd_end += 1
                    continue
                
                if line[cmd_end] == '(' and not sub_escaped:
                    paren_count += 1
                elif line[cmd_end] == ')' and not sub_escaped:
                    paren_count -= 1
                elif line[cmd_end] == '\\':
                    sub_escaped = True
                
                cmd_end += 1
                
                if cmd_end >= len(line) and paren_count > 0:
                    raise ValueError("Unterminated command substitution")
            
            cmd_end -= 1  # adjust for the last increment
            
            # Create a substitution token with the entire $() expression
            self.tokens.append(create_substitution_token(line[i:cmd_end + 1]))
            return cmd_end + 1
            
        if i + 1 < len(line):
            # Check for variable name followed by closing paren
            if ')' in line[i:]:
                var_end = i + 1
                while var_end < len(line) and line[var_end].isalnum():
                    var_end += 1
                
                # If we found a variable name followed by a closing paren
                if var_end < len(line) and line[var_end] == ')':
                    if self.buffer:
                        self.tokens.append(create_word_token(''.join(self.buffer)))
                        self.buffer = []
                    
                    # Add as a single token
                    self.tokens.append(create_word_token(line[i:var_end+1]))
                    return var_end + 1
        
        # For other variables or $ at the end, just add to buffer
        self.buffer.append('$')
        return i + 1
    
    def handle_backtick_substitution(self, line: str, i: int) -> int:
        """Handle backtick command substitution (`command`)"""
        # In single quotes, treat backtick as literal
        if self.in_single_quote:
            self.buffer.append('`')
            return i + 1
            
        # In double quotes, we still need to process backtick substitution
        # but we'll keep the backticks in the token
        if self.in_double_quote:
            self.buffer.append('`')
            return i + 1
        
        # Finish current token if any
        if self.buffer:
            self.tokens.append(create_word_token(''.join(self.buffer)))
            self.buffer = []
        
        # Find matching backtick
        cmd_start = i + 1
        cmd_end = cmd_start
        back_escaped = False
        
        while cmd_end < len(line):
            if back_escaped:
                back_escaped = False
                cmd_end += 1
                continue
            
            if line[cmd_end] == '`' and not back_escaped:
                break
            elif line[cmd_end] == '\\':
                back_escaped = True
            
            cmd_end += 1
        
        if cmd_end >= len(line):
            # Handle unclosed backtick
            self.tokens.append(create_word_token('`' + line[cmd_start:]))
            return len(line)
            
        # Create a substitution token with the command including backticks
        cmd = line[i:cmd_end+1]
        self.tokens.append(create_substitution_token(cmd))
            
        return cmd_end + 1
    
    def handle_stderr_redirection(self, line: str, i: int) -> int:
        """Handle 2> or 2>> redirection operators"""
        # Finish current token if any
        if self.buffer:
            self.tokens.append(create_word_token(''.join(self.buffer)))
            self.buffer = []
        
        next_char = line[i + 1]
        
        # Check for 2>&1 pattern
        if next_char == '>' and i + 2 < len(line) and line[i + 2] == '&' and i + 3 < len(line) and line[i + 3] == '1':
            # Split into separate tokens for 2>&1
            self.tokens.append(create_operator_token('2>'))
            self.tokens.append(create_operator_token('&1'))
            return i + 4
            
        # Check for 2>> append redirection
        if next_char == '>' and i + 2 < len(line) and line[i + 2] == '>':
            self.tokens.append(create_operator_token('2>>'))
            return i + 3
            
        # Handle basic 2> redirection
        self.tokens.append(create_operator_token('2>'))
        return i + 2
    
    def handle_operator(self, line: str, i: int) -> int:
        """Handle shell operators like |, >, &, etc."""
        # Finish current token if any
        if self.buffer:
            self.tokens.append(create_word_token(''.join(self.buffer)))
            self.buffer = []
        
        char = line[i]
        
        # Check for multi-character operators
        if i + 1 < len(line):
            next_char = line[i + 1]
            two_char_op = char + next_char
            
            if two_char_op in self.multi_char_operators:
                self.tokens.append(create_operator_token(two_char_op))
                return i + 2
        
        # Single character operator
        self.tokens.append(create_operator_token(char))
        return i + 1
    
    def handle_brace_expansion(self, line: str, i: int) -> int:
        """
        Handle brace expansion patterns like {a,b,c} or {1..5}
        
        This function attempts to capture the entire brace expansion pattern as a single token,
        including nested braces and multiple patterns (e.g., file{1..3}.{txt,log}).
        """
        # We'll collect the entire token, which may include multiple brace patterns
        start_index = i
        
        # Process the token until we hit a terminating character (space, operator, etc.)
        # Keep track of brace nesting level
        brace_level = 0
        
        # Process until we hit a token-terminating character
        while i < len(line):
            char = line[i]
            
            # Check for token terminators (space, operators, etc.)
            if char.isspace() or char in ';|&<>':
                break
                
            # Handle escaped characters
            if char == '\\' and i + 1 < len(line):
                # Add both the escape and the next character
                self.buffer.append(char)
                i += 1
                if i < len(line):
                    self.buffer.append(line[i])
                i += 1
                continue
            
            # Track brace nesting
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1
            
            # Add the character to our buffer
            self.buffer.append(char)
            i += 1
        
        # If we have unbalanced braces, that's a syntax error, but we'll still
        # tokenize what we have and let the parser handle the error
        if brace_level != 0:
            print(f"Warning: Unbalanced braces in pattern: {''.join(self.buffer)}", file=sys.stderr)
            
        # Create a token for the entire pattern
        if self.buffer:
            token = create_word_token(''.join(self.buffer))
            self.tokens.append(token)
            self.buffer = []
            
        return i

    def finish_current_token(self, i: int) -> int:
        """Complete the current token and add it to the token list"""
        if self.buffer:
            self.tokens.append(create_word_token(''.join(self.buffer)))
            self.buffer = []
        return i
    
    def identify_keywords(self):
        """Mark tokens that are shell keywords"""
        for i, token in enumerate(self.tokens):
            if token.token_type == TokenType.WORD and token.value in KEYWORDS:
                self.tokens[i] = Token(token.value, TokenType.KEYWORD)


def tokenize(line: str) -> List[Token]:
    """Tokenize a shell command line"""
    lexer = Lexer()
    return lexer.tokenize(line)

