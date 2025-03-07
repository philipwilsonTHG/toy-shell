#!/usr/bin/env python3
"""
Simplified test script for the new parser.
"""

from src.parser.token_types import Token, TokenType 
from src.parser.lexer import tokenize
from src.parser.parser.shell_parser import ShellParser

# Initialize parser
parser = ShellParser()

# Test simple command
tokens = tokenize("echo hello world")
result = parser.parse(tokens)
print(f"Simple command: {result}")

# Test pipeline
tokens = tokenize("ls -l | grep test")
result = parser.parse(tokens)
print(f"Pipeline: {result}")

# Test if statement
tokens = tokenize("if test -f /etc/passwd; then echo found; fi")
result = parser.parse(tokens)
print(f"If statement: {result}")

# Test while loop
tokens = tokenize("while true; do echo loop; done")
result = parser.parse(tokens)
print(f"While loop: {result}")

# Test for loop
tokens = tokenize("for i in 1 2 3; do echo $i; done")
result = parser.parse(tokens)
print(f"For loop: {result}")

# Test case statement
tokens = tokenize("case $1 in a) echo A;; b) echo B;; esac")
result = parser.parse(tokens)
print(f"Case statement: {result}")

# Test function definition
tokens = tokenize("function hello() { echo hello; }")
result = parser.parse(tokens)
print(f"Function definition: {result}")
