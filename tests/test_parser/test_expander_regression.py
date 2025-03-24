#!/usr/bin/env python3
"""
Regression tests for special cases that were previously handled in the facade.
Now uses StateMachineExpander directly.
"""

import os
import pytest
from src.parser.state_machine_expander import StateMachineExpander

# Create an expander instance for tests
_expander = StateMachineExpander(os.environ.get)

# Use the expander's methods directly
expand_variables = _expander.expand_variables
expand_all = _expander.expand_all
expand_command_substitution = _expander.expand_command
expand_arithmetic = _expander.expand_arithmetic


@pytest.fixture
def setup_env():
    """Set up test environment variables"""
    old_env = os.environ.copy()
    os.environ.update({
        'TEST_VAR': 'test_value',
        'LONG_VAR': 'abcdefghijk',
        'NESTED': '$TEST_VAR'
    })
    yield
    os.environ.clear()
    os.environ.update(old_env)


def test_nested_variable_expansion(setup_env):
    """Test nested variable expansion regression"""
    # In standard bash, variables are not recursively expanded during variable expansion
    assert expand_variables('$NESTED') == '$TEST_VAR'  # No recursive expansion by default
    
    # The current behavior for ${NESTED} is to do recursive expansion
    assert expand_variables('${NESTED}') == 'test_value'


def test_variable_assign_default(setup_env):
    """Test ${VAR:=default} behavior"""
    # Test assigning a default value to a new variable
    assert 'NEW_VAR' not in os.environ
    
    # Expansion should set the variable and return the value
    assert expand_variables('${NEW_VAR:=default_value}') == 'default_value'
    
    # Verify the variable was actually set
    assert os.environ['NEW_VAR'] == 'default_value'


def test_variable_error_if_unset(setup_env):
    """Test ${VAR:?error} behavior"""
    # Test error if variable is unset
    with pytest.raises(ValueError):
        expand_variables('${UNDEFINED_VAR:?error message}')


def test_substring_extraction(setup_env):
    """Test substring extraction behavior"""
    # Extract 3 chars starting at index 2
    assert expand_variables('${LONG_VAR:2:3}') == 'cde'
    
    # The behavior for ${LONG_VAR:5} used to return the full string
    assert expand_variables('${LONG_VAR:5}') == 'abcdefghijk'


def test_arithmetic_ternary(setup_env):
    """Test arithmetic ternary operator"""
    # Ternary operator inside arithmetic expansion
    assert expand_arithmetic('$((10 > 5 ? 1 : 0))') == '1'
    assert expand_arithmetic('$((10 < 5 ? 1 : 0))') == '0'


def test_quoted_expansions(setup_env):
    """Test quoted expansions regression"""
    # Double quotes allow variable expansion
    assert expand_all('"$TEST_VAR"') == 'test_value'
    
    # Single quotes prevent expansion
    assert expand_all("'$TEST_VAR'") == '$TEST_VAR'
    
    # Double quotes with arithmetic
    assert expand_all('"The result is $(( 10 * 5 ))"') == 'The result is 50'
    
    # Double quotes with command substitution
    assert expand_all('"Result: $(echo test)"') == 'Result: test'