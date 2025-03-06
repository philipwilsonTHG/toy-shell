#!/usr/bin/env python3
"""
Test the new parser's error handling capabilities.
"""

from src.parser.new.lexer import tokenize
from src.parser.new.parser.shell_parser import ShellParser
# No need for ParserContext import as we use parser.context

def test_error_reporting():
    """Test that the parser reports errors correctly."""
    test_cases = [
        "if test -f /etc/passwd; echo found; fi",  # Missing 'then'
        "while true; echo loop; done",  # Missing 'do'
        "for i in 1 2 3; echo $i; done",  # Missing 'do'
        "case $1 in a) echo A; b) echo B; esac",  # Missing ';;' after pattern action
        "function hello() { echo hello",  # Missing closing '}'
        "if test -f /etc/passwd; then echo found",  # Missing 'fi'
        "if test -f /etc/passwd",  # Incomplete if statement
    ]
    
    for i, input_line in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i}: {input_line!r} ===")
        
        # Parse with the new parser
        parser = ShellParser()
        tokens = tokenize(input_line)
        
        # Attempt to parse
        result = parser.parse(tokens)
        
        # If parsing succeeded despite errors, context should have errors
        if result is not None:
            print(f"Parsing succeeded with AST: {result}")
        else:
            print("Parsing failed with no AST produced")
            
        # Print reported errors
        print("\nErrors reported:")
        if parser.context.errors:
            for i, error in enumerate(parser.context.errors, 1):
                print(f"  Error {i}: {error.message}")
                if error.suggestion:
                    print(f"    Suggestion: {error.suggestion}")
        else:
            print("  No errors reported (unexpected)")

if __name__ == "__main__":
    test_error_reporting()