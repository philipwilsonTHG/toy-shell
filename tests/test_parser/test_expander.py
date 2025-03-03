import os
import pytest
from src.parser.expander import (
    expand_variables,
    expand_command_substitution,
    expand_tilde,
    expand_wildcards,
    expand_all
)

@pytest.fixture
def setup_env(temp_env):
    """Set up test environment variables"""
    os.environ.update({
        'TEST_VAR': 'test_value',
        'PATH': '/usr/bin:/bin',
        'HOME': '/home/test',
        'USER': 'testuser'
    })

def test_basic_variable_expansion(setup_env):
    """Test basic variable expansion"""
    assert expand_variables('$TEST_VAR') == 'test_value'
    assert expand_variables('${TEST_VAR}') == 'test_value'
    assert expand_variables('prefix_$TEST_VAR') == 'prefix_test_value'
    assert expand_variables('$TEST_VAR_suffix') == '_suffix'  # No var named TEST_VAR_suffix

def test_nested_variable_expansion(setup_env):
    """Test nested variable expansion"""
    os.environ['NESTED'] = '$TEST_VAR'
    assert expand_variables('$NESTED') == '$TEST_VAR'  # No recursive expansion
    assert expand_variables('${NESTED}') == '$TEST_VAR'

def test_variable_expansion_with_modifiers(setup_env):
    """Test variable expansion with modifiers"""
    # Substring
    os.environ['LONG_VAR'] = 'abcdefghijk'
    assert expand_variables('${LONG_VAR:2:3}') == 'cde'
    assert expand_variables('${LONG_VAR:5}') == 'fghijk'
    
    # Default values
    assert expand_variables('${NONEXISTENT:-default}') == 'default'
    assert expand_variables('${TEST_VAR:-default}') == 'test_value'
    
    # Assign default
    assert expand_variables('${NEW_VAR:=default_value}') == 'default_value'
    assert os.environ['NEW_VAR'] == 'default_value'

def test_command_substitution(temp_env):
    """Test command substitution"""
    # Simple command
    result = expand_command_substitution('$(echo hello)')
    assert result == 'hello'
    
    # Command with arguments
    result = expand_command_substitution('$(echo "test message")')
    assert result == 'test message'
    
    # Command with path
    result = expand_command_substitution('$(pwd)')
    assert os.path.exists(result)
    
    # Failed command
    assert expand_command_substitution('$(nonexistent_command)') == ''
    
    # Command with exit code
    assert expand_command_substitution('$(exit 1)') == ''

def test_nested_command_substitution(temp_env):
    """Test nested command substitution"""
    # Nested commands are processed one at a time
    result = expand_command_substitution('$(echo "$(echo nested)")')
    assert result == '$(echo nested)'
    
    # Multiple substitutions in one line
    result = expand_command_substitution('$(echo foo) $(echo bar)')
    assert result == 'foo $(echo bar)'

def test_tilde_expansion():
    """Test tilde expansion"""
    os.environ['HOME'] = '/home/testuser'
    
    assert expand_tilde('~') == '/home/testuser'
    assert expand_tilde('~/documents') == '/home/testuser/documents'
    assert expand_tilde('file.txt') == 'file.txt'  # No tilde to expand
    assert expand_tilde('~nonexistentuser') == '~nonexistentuser'  # Invalid user

def test_wildcard_expansion(tmp_path):
    """Test wildcard expansion"""
    # Create test files
    (tmp_path / 'test1.txt').touch()
    (tmp_path / 'test2.txt').touch()
    (tmp_path / 'other.log').touch()
    
    os.chdir(tmp_path)
    
    # Test patterns
    assert len(expand_wildcards('*.txt')) == 2
    assert 'test1.txt' in expand_wildcards('test*.txt')
    assert 'other.log' in expand_wildcards('*')
    assert expand_wildcards('nonexistent*') == ['nonexistent*']

def test_quoted_expansion(setup_env):
    """Test expansion with quotes"""
    # Single quotes prevent expansion
    assert expand_all("'$TEST_VAR'") == '$TEST_VAR'
    
    # Double quotes allow variable expansion
    assert expand_all('"$TEST_VAR"') == 'test_value'
    
    # Mixed quotes
    assert expand_all("'quoted \"$TEST_VAR\" string'") == 'quoted "$TEST_VAR" string'

def test_combined_expansion(setup_env, tmp_path):
    """Test multiple types of expansion together"""
    os.chdir(tmp_path)
    (tmp_path / 'test.txt').write_text('content')
    
    # Variable + command substitution
    result = expand_all('$TEST_VAR-$(echo test)')
    assert result == 'test_value-test'
    
    # Tilde + variable
    result = expand_all('~/path/$TEST_VAR')
    assert result == '/home/test/path/test_value'
    
    # Command substitution + wildcards
    result = expand_all('$(echo *)')
    assert 'test.txt' in result
    
    # Multiple substitutions
    result = expand_all('$(echo $TEST_VAR) in $(pwd)')
    assert 'test_value' in result and str(tmp_path) in result
    
    # Quoted substitutions
    result = expand_all('"Value: $(echo $TEST_VAR)"')
    assert result == 'Value: test_value'

def test_error_handling():
    """Test error handling in expansion"""
    # Invalid variable reference
    assert expand_variables('${VAR:}') == ''
    
    # Invalid modifier
    assert expand_variables('${VAR:invalid}') == ''
    
    # Unclosed brace
    assert expand_variables('${VAR') == '${VAR'
    
    # Invalid command substitution
    assert expand_command_substitution('$(invalid command)') == ''

def test_special_cases(setup_env):
    """Test special expansion cases"""
    # Empty variable
    os.environ['EMPTY'] = ''
    assert expand_variables('$EMPTY') == ''
    assert expand_variables('${EMPTY:-default}') == 'default'
    
    # Variable with spaces
    os.environ['SPACED'] = 'value with spaces'
    assert expand_variables('$SPACED') == 'value with spaces'
    
    # Multiple variables in one string
    assert expand_variables('$TEST_VAR:$PATH') == 'test_value:/usr/bin:/bin'
