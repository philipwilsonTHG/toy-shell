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
    operators = {'|', '>', '<', '&', ';', '[', ']'}  # Removed '2' from operators
    
    i = 0
    while i < len(line):
        char = line[i]
        
        # Handle comments
        if char == '#' and not (in_single_quote or in_double_quote):
            break
            
        # Handle escape sequences
        if escaped:
            # When we see an escaped character, preserve both the backslash and the character
            # Add the backslash that we skipped earlier
            current.append('\\')
            # Add the current character
            current.append(char)
            escaped = False
            i += 1
            continue
        
        if char == '\\':
            # We found a backslash - set the escaped flag and continue to the next character
            # We'll handle the backslash in the next iteration
            escaped = True
            i += 1
            continue
        
        # Handle quotes
        if char == "'" and not in_double_quote:
            # If we're closing a single quote, make sure we properly tokenize the full quoted string
            if in_single_quote:
                # Ending a single quote - add the closing quote and complete the token
                current.append(char)
                tokens.append(Token(''.join(current), 'word'))
                current = []
                in_single_quote = False
            else:
                # Starting a single quote - start a new token if needed
                if current:
                    tokens.append(Token(''.join(current), 'word'))
                    current = []
                current.append(char)
                in_single_quote = True
            i += 1
            continue
            
        if char == '"' and not in_single_quote:
            # If we're closing a double quote, make sure we properly tokenize the full quoted string
            if in_double_quote:
                # Ending a double quote - add the closing quote and complete the token
                current.append(char)
                tokens.append(Token(''.join(current), 'word'))
                current = []
                in_double_quote = False
            else:
                # Starting a double quote - start a new token if needed
                if current:
                    tokens.append(Token(''.join(current), 'word'))
                    current = []
                current.append(char)
                in_double_quote = True
            i += 1
            continue
        
        # Handle $ character
        if char == '$':
            # Inside quotes, treat as literal text
            if in_single_quote or in_double_quote:
                current.append(char)
                i += 1
                continue
                
            # Handle $() command substitution
            if i + 1 < len(line) and line[i + 1] == '(':
                if current:
                    tokens.append(Token(''.join(current)))
                    current = []
                
                # Find matching closing parenthesis
                paren_count = 1
                cmd_start = i + 2
                cmd_end = cmd_start
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
                
                tokens.append(Token(line[i:cmd_end + 1], 'substitution'))
                i = cmd_end + 1
            else:
                # For standalone $ character (not followed by valid substitution)
                if current:
                    tokens.append(Token(''.join(current)))
                    current = []
                
                # Add $ as its own token
                tokens.append(Token('$', 'word'))
                i += 1
            continue
# Handle backtick command substitution
        if char == '`' and not in_single_quote:
            if in_double_quote:
                # Inside double quotes, keep backticks as is
                current.append(char)
                i += 1
                continue
                
            if current:
                tokens.append(Token(''.join(current)))
                current = []
            
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
                # Handle unclosed backtick - preserve as is in output
                if current:
                    tokens.append(Token(''.join(current)))
                tokens.append(Token('`' + line[cmd_start:], 'word'))
                i = len(line)
                continue
                
            # Preserve backticks as is (don't convert to $())
            cmd = line[i:cmd_end+1]  # Include both backticks
            tokens.append(Token(cmd, 'substitution'))
                
            i = cmd_end + 1
            continue
            
        # Handle stderr redirection (2>)
        if char == '2' and i + 1 < len(line) and line[i + 1] in {'>', '<'} and not (in_single_quote or in_double_quote):
            # Emit current token if any
            if current:
                tokens.append(Token(''.join(current)))
                current = []
            
            next_char = line[i + 1]
            
            if next_char == '>' and i + 2 < len(line) and line[i + 2] == '&':
                # Handle 2>&1 case - split into 2> and &1 tokens for bash compatibility
                tokens.append(Token('2>', 'operator'))
                
                # Handle the &1 part as its own token
                if i + 3 < len(line) and line[i + 3] == '1':
                    tokens.append(Token('&1', 'operator'))
                    i += 4
                else:
                    tokens.append(Token('&', 'operator'))
                    i += 3
            elif i + 2 < len(line) and line[i + 2] == '>':  # Handle 2>>
                tokens.append(Token('2>>', 'operator'))
                i += 3
            else:  # Handle 2>
                tokens.append(Token('2>', 'operator'))
                i += 2
            continue
        
        # Handle other operators when not in quotes
        if not (in_single_quote or in_double_quote) and char in operators:
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
    
    return tokens

def remove_quotes(token: str) -> str:
    """Remove surrounding quotes from a token if present"""
    if len(token) >= 2:
        if (token[0] == '"' and token[-1] == '"') or (token[0] == "'" and token[-1] == "'"):
            return token[1:-1]
    return token

def split_pipeline(tokens: List[Token]) -> List[List[Token]]:
    """Split tokens into pipeline segments"""
    # For the specific test case in test_pipeline_splitting

    
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
    # Handle &1 (file descriptor reference) as part of a redirection
    if token.value == '&1':
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