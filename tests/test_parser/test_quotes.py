import pytest
from src.parser.quotes import (
    handle_quotes,
    is_quoted,
    strip_quotes,
    find_matching_quote,
    split_by_unquoted
)

def test_handle_quotes_basic():
    """Test basic quote handling"""
    # No quotes
    text, in_single, in_double = handle_quotes("simple text")
    assert text == "simple text"
    assert not in_single
    assert not in_double
    
    # Single quotes
    text, in_single, in_double = handle_quotes("'quoted text'")
    assert text == "'quoted text'"
    assert not in_single  # Complete quote pair
    assert not in_double

def test_handle_quotes_nested():
    """Test nested quotes handling"""
    # Double quotes inside single quotes
    text, in_single, in_double = handle_quotes("'text \"with\" quotes'")
    assert text == "'text \"with\" quotes'"
    assert not in_single
    assert not in_double
    
    # Single quotes inside double quotes
    text, in_single, in_double = handle_quotes('"text \'with\' quotes"')
    assert text == '"text \'with\' quotes"'
    assert not in_single
    assert not in_double

def test_handle_quotes_escapes():
    """Test escaped quotes handling"""
    # Escaped single quote
    text, in_single, in_double = handle_quotes("text with \\'quote")
    assert text == "text with 'quote"
    assert not in_single
    assert not in_double
    
    # Escaped double quote
    text, in_single, in_double = handle_quotes('text with \\"quote')
    assert text == 'text with "quote'
    assert not in_single
    assert not in_double

def test_handle_quotes_unclosed():
    """Test handling of unclosed quotes"""
    # Unclosed single quote
    text, in_single, in_double = handle_quotes("text 'unclosed")
    assert text == "text 'unclosed"
    assert in_single
    assert not in_double
    
    # Unclosed double quote
    text, in_single, in_double = handle_quotes('text "unclosed')
    assert text == 'text "unclosed'
    assert not in_single
    assert in_double

def test_is_quoted():
    """Test quote detection"""
    assert is_quoted('"quoted"')
    assert is_quoted("'quoted'")
    assert not is_quoted("unquoted")
    assert not is_quoted('"half quoted')
    assert not is_quoted("'")  # Single quote mark
    assert is_quoted('""')  # Empty quotes are still quoted
    assert is_quoted("''")  # Empty single quotes

def test_strip_quotes():
    """Test quote stripping"""
    assert strip_quotes('"quoted"') == 'quoted'
    assert strip_quotes("'quoted'") == 'quoted'
    assert strip_quotes("unquoted") == 'unquoted'
    assert strip_quotes('"half quoted') == '"half quoted'
    assert strip_quotes("") == ""
    assert strip_quotes("'") == "'"

def test_find_matching_quote():
    """Test finding matching quotes"""
    # Simple quotes
    assert find_matching_quote('"test"', 0) == 5
    assert find_matching_quote("'test'", 0) == 5
    
    # Empty quotes
    assert find_matching_quote('""', 0) == 1
    assert find_matching_quote("''", 0) == 1
    
    # Escaped quotes
    text = r'test \"quote" end'
    assert find_matching_quote(text, text.rindex('"')) == len(text) - 4
    
    # No matching quote
    assert find_matching_quote('"test', 0) == -1
    
    # Invalid start position
    assert find_matching_quote("test", 10) == -1
    
    # Not a quote character
    assert find_matching_quote("test", 0) == -1
    
    # Nested quotes
    assert find_matching_quote('"test \'nested\' quote"', 0) == 19

def test_split_by_unquoted():
    """Test splitting by unquoted delimiter"""
    # Simple split
    assert split_by_unquoted("a,b,c", ",") == ["a", "b", "c"]
    
    # Quoted delimiters
    assert split_by_unquoted('a,"b,c",d', ",") == ['a', '"b,c"', 'd']
    assert split_by_unquoted("a,'b,c',d", ",") == ['a', "'b,c'", 'd']
    
    # Mixed quotes
    assert split_by_unquoted('a,"b,\'c,d\',e",f', ",") == ['a', '"b,\'c,d\',e"', 'f']
    
    # Empty fields
    assert split_by_unquoted("a,,c", ",") == ["a", "", "c"]
    
    # Empty quoted fields
    assert split_by_unquoted('a,"",c', ",") == ['a', '""', 'c']
    assert split_by_unquoted("a,'',c", ",") == ["a", "''", "c"]

def test_split_by_unquoted_errors():
    """Test error handling in split_by_unquoted"""
    # Unclosed quotes
    with pytest.raises(ValueError, match="Unterminated quote"):
        split_by_unquoted('a,"b,c', ",")
    
    # Unclosed nested quotes
    with pytest.raises(ValueError, match="Unterminated quote"):
        split_by_unquoted('a,"b,\'c",d', ",")
    
    # Empty input
    assert split_by_unquoted("", ",") == [""]
    
    # Single character
    assert split_by_unquoted("a", ",") == ["a"]

def test_handle_quotes_special_cases():
    """Test special cases in quote handling"""
    # Empty string
    text, in_single, in_double = handle_quotes("")
    assert text == ""
    assert not in_single
    assert not in_double
    
    # Only escapes
    text, in_single, in_double = handle_quotes("\\\\")
    assert text == "\\\\"  # Preserves escape character
    assert not in_single
    assert not in_double
    
    # Multiple consecutive quotes
    text, in_single, in_double = handle_quotes('""\'\'""')
    assert text == '""\'\'""'
    assert not in_single
    assert not in_double
    
    # Escaped quotes
    text, in_single, in_double = handle_quotes('\\"\\\'')
    assert text == '\\"\\\'', "Should preserve escaped quotes"
    assert not in_single
    assert not in_double

def test_quote_handling_with_spaces():
    """Test quote handling with spaces"""
    # Preserve spaces in quotes
    text, in_single, in_double = handle_quotes('"  spaced  "')
    assert text == '"  spaced  "'
    assert not in_single
    assert not in_double
    
    # Mixed spaces and quotes
    text, in_single, in_double = handle_quotes('  "quoted"  \'quoted\'  ')
    assert text == '  "quoted"  \'quoted\'  '
    assert not in_single
    assert not in_double
