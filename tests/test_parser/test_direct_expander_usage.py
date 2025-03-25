#!/usr/bin/env python3
"""
Tests demonstrating direct usage of the StateMachineExpander class.
This shows the recommended way to use the expander after the facade is deprecated.
"""

import os
import pytest
from src.parser.state_machine_expander import StateMachineExpander


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


@pytest.fixture
def expander(setup_env):
    """Create a StateMachineExpander instance using environment variables"""
    return StateMachineExpander(os.environ.get, debug_mode=False)


def test_variable_expansion(expander):
    """Test variable expansion using the expander directly"""
    # Basic variable expansion
    assert expander.expand_variables('$TEST_VAR') == 'test_value'
    
    # Variable with modifier
    assert expander.expand_variables('${TEST_VAR:-default}') == 'test_value'
    
    # Default value for undefined variable
    assert expander.expand_variables('${UNDEFINED:-default}') == 'default'


def test_command_expansion(expander):
    """Test command expansion using the expander directly"""
    # Simple command
    assert expander.expand_command('$(echo hello)') == 'hello'
    
    # Command with arguments
    assert expander.expand_command('$(echo "test message")') == 'test message'


def test_arithmetic_expansion(expander):
    """Test arithmetic expansion using the expander directly"""
    # Simple arithmetic
    assert expander.expand_arithmetic('$((1 + 2))') == '3'
    
    # Complex arithmetic
    assert expander.expand_arithmetic('$((10 > 5 ? 1 : 0))') == '1'


def test_tilde_expansion(expander):
    """Test tilde expansion using the expander directly"""
    # Get the expected home directory
    home = os.environ.get('HOME', '')
    
    # Expand tilde
    assert expander.expand_tilde('~') == home
    
    # Expand tilde with path
    assert expander.expand_tilde('~/documents') == f'{home}/documents'


def test_full_expansion(expander):
    """Test full expansion using the expander directly"""
    # Mixed expansion
    result = expander.expand_all_with_brace_expansion('$TEST_VAR is $(echo testing)')
    assert result == 'test_value is testing'
    
    # Quoted expansions
    assert expander.expand('"$TEST_VAR"') == 'test_value'
    assert expander.expand("'$TEST_VAR'") == '$TEST_VAR'
    
    # Preservation of spaces in quoted strings with expansion
    assert expander.expand('"The result is $(( 10 * 5 ))"') == 'The result is 50'
    

def test_reusing_expander_performance():
    """Demonstrate reusing an expander instance for performance"""
    # Create a custom scope
    variables = {
        'VAR1': 'value1',
        'VAR2': 'value2',
        'COMBINED': '$VAR1 and $VAR2'
    }
    
    # Create a scope provider function that handles recursive expansion
    def get_var(name):
        value = variables.get(name)
        if value and '$' in value:
            # Create a temporary expander to expand the variable value
            temp_expander = StateMachineExpander(get_var, False)
            return temp_expander.expand_variables(value)
        return value
    
    # Create a StateMachineExpander with the custom scope
    expander = StateMachineExpander(get_var)
    
    # Use the same expander for multiple operations
    assert expander.expand_variables('$VAR1') == 'value1'
    assert expander.expand_variables('$VAR2') == 'value2'
    assert expander.expand_variables('$COMBINED') == 'value1 and value2'


def test_integration_example():
    """Test an integrated example of expander usage"""
    # Create a custom function that processes a command with arguments
    def process_command(command_line, expander):
        # Split the command into words
        words = command_line.split()
        if not words:
            return []
            
        # The first word is the command, expand variables
        command = expander.expand_variables(words[0])
        
        # The rest are arguments, do full expansion
        args = [expander.expand_all_with_brace_expansion(arg) for arg in words[1:]]
        
        # Return the processed command and args
        return [command] + args
    
    # Create a test scope
    variables = {
        'CMD': 'echo',
        'ARG': 'hello world',
        'HOME': '/home/user'
    }
    
    # Create an expander with the test scope
    expander = StateMachineExpander(variables.get)
    
    # Process a command line
    processed = process_command('$CMD $ARG ~/test', expander)
    
    # Verify the results
    assert processed == ['echo', 'hello world', '/home/user/test']