#!/usr/bin/env python3

"""
Test script to verify that the compatibility layer works with the existing code.
"""

import sys

def test_old_lexer():
    """Test the original lexer implementation"""
    # Note: This function is now completely obsolete as we've removed all compatibility imports
    # We now import directly from the new modules
    from src.parser.new.token_types import Token, TokenType
    from src.parser.new.lexer import tokenize
    from src.parser.new.redirection import RedirectionParser
    
    # For compatibility with the test
    parse_redirections = RedirectionParser.parse_redirections
    split_pipeline = RedirectionParser.split_pipeline
    
    print("\n=== Testing direct imports from new modules ===")
    
    # Test basic tokenization
    line = 'ls -la /nonexistant > /tmp/out.txt 2>&1'
    tokens = tokenize(line)
    print("Direct import tokens:")
    for i, token in enumerate(tokens):
        print(f"  Token {i}: '{token.value}' ({token.token_type})")
    
    # Test redirection parsing
    cmd_tokens, redirections = parse_redirections(tokens)
    print("\nAfter parsing redirections:")
    print("Command tokens:")
    for i, token in enumerate(cmd_tokens):
        print(f"  Token {i}: '{token.value}' ({token.token_type})")
    print("Redirections:")
    for op, target in redirections:
        print(f"  {op} -> {target}")
    
    # Test pipeline splitting
    line = 'grep "pattern" file.txt | sort | uniq'
    tokens = tokenize(line)
    segments = split_pipeline(tokens)
    print("\nPipeline segments:")
    for i, segment in enumerate(segments):
        print(f"Segment {i}:")
        for j, token in enumerate(segment):
            print(f"  Token {j}: '{token.value}' ({token.token_type})")

def test_new_lexer_compatibility():
    """Test the new lexer API directly"""
    from src.parser.new.token_types import Token, TokenType
    from src.parser.new.lexer import tokenize
    from src.parser.new.redirection import RedirectionParser
    
    # Aliases for compatibility with original test
    parse_redirections = RedirectionParser.parse_redirections
    split_pipeline = RedirectionParser.split_pipeline
    
    print("\n=== Testing new lexer API directly ===")
    
    # Test basic tokenization
    line = 'ls -la /nonexistant > /tmp/out.txt 2>&1'
    tokens = tokenize(line)
    print("New lexer tokens (direct API):")
    for i, token in enumerate(tokens):
        print(f"  Token {i}: '{token.value}' ({token.token_type})")
    
    # Test redirection parsing
    cmd_tokens, redirections = parse_redirections(tokens)
    print("\nAfter parsing redirections:")
    print("Command tokens:")
    for i, token in enumerate(cmd_tokens):
        print(f"  Token {i}: '{token.value}' ({token.token_type})")
    print("Redirections:")
    for op, target in redirections:
        print(f"  {op} -> {target}")
    
    # Test pipeline splitting
    line = 'grep "pattern" file.txt | sort | uniq'
    tokens = tokenize(line)
    segments = split_pipeline(tokens)
    print("\nPipeline segments:")
    for i, segment in enumerate(segments):
        print(f"Segment {i}:")
        for j, token in enumerate(segment):
            print(f"  Token {j}: '{token.value}' ({token.token_type})")

if __name__ == "__main__":
    try:
        test_old_lexer()
    except Exception as e:
        print(f"Error testing old lexer: {e}")
    
    try:
        test_new_lexer_compatibility()
    except Exception as e:
        print(f"Error testing new lexer compatibility: {e}")
        import traceback
        traceback.print_exc()