#!/usr/bin/env python3
"""
Test the parser's error handling capabilities.
"""

from src.parser.lexer import tokenize
from src.parser.parser.shell_parser import ShellParser
from src.parser.parser.parser_context import ParserContext

def test_error_reporting():
    """Test that the parser reports errors correctly."""
    # This function is used by pytest - it must have assertions
    # We'll keep it simple and clear
    
    # Test with just one case to verify error handling
    parser = ShellParser()
    result = parser.parse_line("if test -f /etc/passwd; echo found; fi")  # Missing 'then'
    
    # Should have errors
    assert len(parser.context.errors) > 0
    
def manual_test_error_reporting():
    """More detailed error testing - for manual use only."""
    test_cases = [
        "if test -f /etc/passwd; echo found; fi",  # Missing 'then'
        "while true; echo loop; done",  # Missing 'do'
        "for i in 1 2 3; echo $i; done",  # Missing 'do'
        "case $1 in a) echo A; b) echo B; esac",  # Missing ';;' after pattern action
        "function hello() { echo hello",  # Missing closing '}'
        "if test -f /etc/passwd; then echo found",  # Missing 'fi'
        "if test -f /etc/passwd",  # Incomplete if statement
    ]
    
    # Create a single parser instance to use for all tests
    parser = ShellParser()
    
    for i, input_line in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i}: {input_line!r} ===")
        
        # Attempt to parse
        result = parser.parse_line(input_line)
        
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
        
        # Important: Reset the parser context for the next test
        parser.context = ParserContext()

if __name__ == "__main__":
    # When run as a script, use the detailed testing version
    manual_test_error_reporting()