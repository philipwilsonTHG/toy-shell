#!/usr/bin/env python3
from src.parser.lexer import tokenize
from src.parser.quotes import is_quoted, strip_quotes

# Test a command with quoted arguments
cmd = './show_args.py "hello world" "second argument" normal_arg "mixed arg"'
tokens = tokenize(cmd)

print(f"Number of tokens: {len(tokens)}")
for i, token in enumerate(tokens):
    print(f"Token {i}: value={repr(token.value)} type={token.token_type}")
    print(f"  - is_quoted: {is_quoted(token.value)}")
    print(f"  - stripped: {repr(strip_quotes(token.value))}")
