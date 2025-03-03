#!/usr/bin/env python3

from typing import List, Tuple
from .quotes import is_quoted, strip_quotes

class Token:
    """Represents a shell token with type information"""
    
    def __init__(self, value: str, token_type: str = 'word'):
        self.value = value
        self.type = token_type
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Token({self.value!r}, {self.type!r})"

def tokenize(line: str) -> List[Token]:
    """Tokenize a command line into shell tokens
    
    Handles:
    - Word splitting
    - Quote handling
    - Operator recognition
    - Comment handling
    """
    tokens = []
    current = []
    in_single_quote = False
    in_double_quote = False
    escaped = False
    
    # Special characters that form operators
    operators = {'|', '>', '<', '&', ';', '[', ']', '2'}  # Added '2' for stderr
    
    # Command substitution state
    in_substitution = False
    
    i = 0
    while i < len(line):
        char = line[i]
        
        # Handle comments
        if char == '#' and not (in_single_quote or in_double_quote):
            break
        
        # Handle escape sequences
        if escaped:
            current.append(char)
            escaped = False
            i += 1
            continue
        
        if char == '\\':
            escaped = True
            i += 1
            continue
        
        # Handle quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
            i += 1
            continue
            
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
            i += 1
            continue
        
        # Handle $() command substitution
        if char == '$' and i + 1 < len(line) and line[i + 1] == '(':
            if current:
                tokens.append(Token(''.join(current)))
                current = []
            
            # Find matching closing parenthesis
            paren_count = 1
            cmd_start = i + 2
            cmd_end = cmd_start
            
            while cmd_end < len(line) and paren_count > 0:
                if line[cmd_end] == '(' and not escaped:
                    paren_count += 1
                elif line[cmd_end] == ')' and not escaped:
                    paren_count -= 1
                elif line[cmd_end] == '\\':
                    escaped = True
                else:
                    escaped = False
                if paren_count > 0:
                    cmd_end += 1
            
            if paren_count == 0:
                # Keep substitution as a single token
                tokens.append(Token(line[i:cmd_end + 1], 'substitution'))
                i = cmd_end + 1
                continue
            else:
                # Handle unclosed substitution
                current.extend(['$', '('])
                i += 2
                continue
        
        # Handle backtick command substitution
        if char == '`' and not (in_single_quote or in_double_quote):
            if current:
                tokens.append(Token(''.join(current)))
                current = []
            
            # Find matching backtick
            cmd_start = i + 1
            cmd_end = cmd_start
            
            while cmd_end < len(line):
                if line[cmd_end] == '`' and not escaped:
                    break
                elif line[cmd_end] == '\\':
                    escaped = True
                else:
                    escaped = False
                cmd_end += 1
            
            if cmd_end < len(line):
                # Convert to $() format
                cmd = line[cmd_start:cmd_end]
                tokens.append(Token(f"$({cmd})", 'substitution'))
                i = cmd_end + 1
                continue
            else:
                # Handle unclosed backtick
                current.append('`')
                i += 1
                continue
            
        # Handle operators when not in quotes and not in substitution
        if not (in_single_quote or in_double_quote or in_substitution):
            # Handle stderr redirection (2>)
            if char == '2' and i + 1 < len(line) and line[i + 1] in {'>', '<'}:
                # Emit current token if any
                if current:
                    tokens.append(Token(''.join(current)))
                    current = []
                
                next_char = line[i + 1]
                if i + 2 < len(line) and line[i + 2] == '>':  # Handle 2>>
                    tokens.append(Token('2>>', 'operator'))
                    i += 3
                else:  # Handle 2>
                    tokens.append(Token('2>', 'operator'))
                    i += 2
                continue
            
            # Handle other operators
            if char in operators:
                # Emit current token if any
                if current:
                    tokens.append(Token(''.join(current)))
                    current = []
                
                # Handle multi-character operators
                if i + 1 < len(line):
                    next_char = line[i + 1]
                    if char + next_char in {'&&', '||', '>>', '<<', '>&', '<&', '|&'}:
                        tokens.append(Token(char + next_char, 'operator'))
                        i += 2
                        continue
                
                tokens.append(Token(char, 'operator'))
                i += 1
                continue
        
        # Handle whitespace when not in quotes
        if not (in_single_quote or in_double_quote) and char.isspace():
            if current:
                tokens.append(Token(''.join(current)))
                current = []
            i += 1
            continue
        
        current.append(char)
        i += 1
    
    # Handle any remaining characters
    if current:
        tokens.append(Token(''.join(current)))
    
    # Validate quotes and substitution
    if in_single_quote:
        raise ValueError("Unterminated single quote")
    if in_double_quote:
        raise ValueError("Unterminated double quote")
    if in_substitution:
        raise ValueError("Unterminated command substitution")
    
    return tokens

def remove_quotes(token: str) -> str:
    """Remove surrounding quotes from a token if present"""
    if len(token) >= 2:
        if (token[0] == '"' and token[-1] == '"') or (token[0] == "'" and token[-1] == "'"):
            return token[1:-1]
    return token

def split_pipeline(tokens: List[Token]) -> List[List[Token]]:
    """Split tokens into pipeline segments"""
    segments = []
    current = []
    
    for token in tokens:
        if token.type == 'operator' and token.value == '|':
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    
    if current:
        segments.append(current)
    
    return segments

def is_redirection(token: Token) -> bool:
    """Check if token is a redirection operator"""
    if token.type != 'operator':
        return False
    # Match basic redirections
    if token.value in {'>', '<', '>>', '<<', '>&', '<&'}:
        return True
    # Match stderr redirections
    if token.value in {'2>', '2>>'}:
        return True
    return False

def parse_redirections(tokens: List[Token]) -> Tuple[List[Token], List[Tuple[str, str]]]:
    """Extract redirections from token list
    
    Returns:
        (remaining_tokens, redirections)
        where redirections is a list of (operator, target) tuples
    """
    result = []
    redirections = []
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        if is_redirection(token):
            if i + 1 >= len(tokens):
                raise ValueError(f"Missing target for redirection {token.value}")
            redirections.append((token.value, tokens[i + 1].value))
            i += 2
        else:
            result.append(token)
            i += 1
    
    return result, redirections
