#!/usr/bin/env python3

from src.parser.new.lexer import tokenize
from src.parser.new.redirection import RedirectionParser
from src.parser.new.token_types import TokenType

# Alias functions for compatibility with the rest of the file
parse_redirections = RedirectionParser.parse_redirections
split_pipeline = RedirectionParser.split_pipeline

def print_tokens(tokens):
    """Pretty print tokens for debugging"""
    for i, token in enumerate(tokens):
        # We now always use token_type
        token_type = token.token_type
        print(f"  Token {i}: '{token.value}' ({token_type})")

def test_basic_command():
    """Test a basic command with arguments"""
    line = 'ls -la /home'
    tokens = tokenize(line)
    print("Basic command:")
    print_tokens(tokens)
    print()

def test_quotes():
    """Test quoted strings"""
    line = 'echo "hello world" \'single quoted\''
    tokens = tokenize(line)
    print("Quoted strings:")
    print_tokens(tokens)
    print()
    
def test_redirections():
    """Test redirection handling"""
    line = 'ls /nonexistant > /tmp/out.txt 2>&1'
    tokens = tokenize(line)
    print("Redirection tokens:")
    print_tokens(tokens)
    
    cmd_tokens, redirections = parse_redirections(tokens)
    print("\nAfter parsing redirections:")
    print("Command tokens:")
    print_tokens(cmd_tokens)
    print("Redirections:")
    for op, target in redirections:
        print(f"  {op} -> {target}")
    print()

def test_pipeline():
    """Test pipeline parsing"""
    line = 'grep "pattern" file.txt | sort | uniq -c'
    tokens = tokenize(line)
    print("Pipeline tokens:")
    print_tokens(tokens)
    
    segments = split_pipeline(tokens)
    print("\nPipeline segments:")
    for i, segment in enumerate(segments):
        print(f"Segment {i}:")
        print_tokens(segment)
    print()

if __name__ == "__main__":
    test_basic_command()
    test_quotes()
    test_redirections()
    test_pipeline()