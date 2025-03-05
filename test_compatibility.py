#!/usr/bin/env python3

"""
Test script to verify that the compatibility layer works with the existing code.
"""

import sys

def test_old_lexer():
    """Test the original lexer implementation"""
    # Note: This function is now obsolete since old lexer.py is removed
    # We'll use the parser module directly, which now imports from the new implementation
    from src.parser import Token, tokenize, parse_redirections, split_pipeline
    
    print("\n=== Testing parser module (using new lexer) ===")
    
    # Test basic tokenization
    line = 'ls -la /nonexistant > /tmp/out.txt 2>&1'
    tokens = tokenize(line)
    print("Parser module tokens:")
    for i, token in enumerate(tokens):
        print(f"  Token {i}: '{token.value}' ({token.type})")
    
    # Test redirection parsing
    cmd_tokens, redirections = parse_redirections(tokens)
    print("\nAfter parsing redirections:")
    print("Command tokens:")
    for i, token in enumerate(cmd_tokens):
        print(f"  Token {i}: '{token.value}' ({token.type})")
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
            print(f"  Token {j}: '{token.value}' ({token.type})")

def test_new_lexer_compatibility():
    """Test the new lexer with compatibility layer"""
    from src.parser.new.compatibility import tokenize, parse_redirections, split_pipeline
    
    print("\n=== Testing new lexer with compatibility layer ===")
    
    # Test basic tokenization
    line = 'ls -la /nonexistant > /tmp/out.txt 2>&1'
    tokens = tokenize(line)
    print("New lexer tokens (with compatibility):")
    for i, token in enumerate(tokens):
        print(f"  Token {i}: '{token.value}' ({token.type})")
    
    # Test redirection parsing
    cmd_tokens, redirections = parse_redirections(tokens)
    print("\nAfter parsing redirections:")
    print("Command tokens:")
    for i, token in enumerate(cmd_tokens):
        print(f"  Token {i}: '{token.value}' ({token.type})")
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
            print(f"  Token {j}: '{token.value}' ({token.type})")

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