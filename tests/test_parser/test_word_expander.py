#!/usr/bin/env python3

import pytest
from unittest.mock import MagicMock

from src.parser.word_expander import WordExpander


def test_word_expander_init():
    """Test initialization of WordExpander"""
    # Create a mock scope provider
    scope_provider = lambda name: f"value_{name}"
    
    # Create the expander
    expander = WordExpander(scope_provider)
    
    # Check that the scope provider was stored
    assert expander.scope_provider is scope_provider
    assert expander.debug_mode is False
    
    # Test with debug mode
    expander = WordExpander(scope_provider, debug_mode=True)
    assert expander.debug_mode is True


def test_handle_escaped_dollars():
    """Test handling of escaped dollar signs"""
    expander = WordExpander(lambda _: None)
    
    # Test with no escaped dollars
    assert expander.handle_escaped_dollars("hello") == "hello"
    
    # Test with escaped dollars
    assert expander.handle_escaped_dollars("hello \\$world") == "hello $world"
    assert expander.handle_escaped_dollars("\\$VAR") == "$VAR"


def test_expand_simple_variables():
    """Test expansion of simple variables"""
    # Create a mock scope provider
    scope_provider = lambda name: f"value_{name}" if name not in ["EMPTY", "UNDEFINED"] else ""
    
    # Create the expander
    expander = WordExpander(scope_provider)
    
    # Test simple variable expansion
    assert expander.expand("$VAR") == "value_VAR"
    assert expander.expand("Hello $NAME") == "Hello value_NAME"
    assert expander.expand("$EMPTY") == ""
    assert expander.expand("$UNDEFINED") == ""
    
    # Test with quotes
    assert expander.expand("'$VAR'") == "'$VAR'"  # Single quotes prevent expansion
    assert expander.expand('"$VAR"') == '"value_VAR"'  # Double quotes allow expansion


def test_expand_with_braces():
    """Test expansion of variables with braces"""
    # Create the expander with a scope provider
    expander = WordExpander(lambda name: f"value_{name}")
    
    # Test with brace expansion enabled
    assert "file_a file_b" in expander.expand("file_{a,b}")
    
    # Verify variable expansion works inside braces
    scope_provider = lambda name: "1" if name == "START" else "3" if name == "END" else ""
    expander = WordExpander(scope_provider)
    assert expander.expand("{$START..$END}") in ["1 2 3", "{1..3}"]  # Different implementations may vary


def test_expand_variables_in_context():
    """Test variable expansion in a more complex context"""
    # Variables to provide from the scope
    variables = {
        "HOME": "/home/user",
        "PATH": "/usr/bin:/bin",
        "USER": "testuser",
        "COUNT": "5",
    }
    
    # Create the expander
    expander = WordExpander(lambda name: variables.get(name, ""))
    
    # Test expansion in a command context
    assert expander.expand("echo $USER is using $HOME") == "echo testuser is using /home/user"
    
    # Test with variable used multiple times
    assert expander.expand("$USER:$USER") == "testuser:testuser"
    
    # Test with partial variable names
    assert expander.expand("$USER_NAME") == ""  # Should not match partial name
    
    # Test with numbers
    assert expander.expand("$COUNT items") == "5 items"