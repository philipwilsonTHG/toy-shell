import os
import pytest
from src.builtins.env import export, unset

@pytest.fixture
def temp_env():
    """Set up a clean environment for testing"""
    old_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(old_env)

def test_export_no_args(temp_env, capsys):
    """Test export command with no arguments lists environment"""
    # Set some test variables
    os.environ['TEST_VAR1'] = 'value1'
    os.environ['TEST_VAR2'] = 'value2'
    
    export()
    captured = capsys.readouterr()
    
    # Check that our test variables are listed
    assert 'TEST_VAR1=value1' in captured.out
    assert 'TEST_VAR2=value2' in captured.out

def test_export_set_variable(temp_env):
    """Test setting variables with export"""
    export('NEW_VAR=test_value')
    assert os.environ['NEW_VAR'] == 'test_value'
    
    # Test overwriting existing variable
    export('NEW_VAR=updated_value')
    assert os.environ['NEW_VAR'] == 'updated_value'

def test_export_multiple_variables(temp_env):
    """Test setting multiple variables at once"""
    export('VAR1=val1', 'VAR2=val2', 'VAR3=val3')
    assert os.environ['VAR1'] == 'val1'
    assert os.environ['VAR2'] == 'val2'
    assert os.environ['VAR3'] == 'val3'

def test_export_quoted_values(temp_env):
    """Test export with quoted values"""
    export('QUOTED="value with spaces"')
    assert os.environ['QUOTED'] == 'value with spaces'
    
    export("SINGLE='quoted value'")
    assert os.environ['SINGLE'] == 'quoted value'

def test_export_invalid_format(temp_env, capsys):
    """Test export with invalid variable format"""
    export('INVALID')  # Missing =value
    captured = capsys.readouterr()
    assert 'not found' in captured.err.lower()
    
    export('=invalid')  # Missing variable name
    captured = capsys.readouterr()
    assert 'invalid format' in captured.err.lower()

def test_unset_variable(temp_env):
    """Test unsetting variables"""
    # Set up test variable
    os.environ['TEST_VAR'] = 'value'
    assert 'TEST_VAR' in os.environ
    
    # Unset it
    unset('TEST_VAR')
    assert 'TEST_VAR' not in os.environ

def test_unset_multiple_variables(temp_env):
    """Test unsetting multiple variables"""
    # Set up test variables
    os.environ.update({
        'VAR1': 'val1',
        'VAR2': 'val2',
        'VAR3': 'val3'
    })
    
    unset('VAR1', 'VAR2', 'VAR3')
    assert 'VAR1' not in os.environ
    assert 'VAR2' not in os.environ
    assert 'VAR3' not in os.environ

def test_unset_nonexistent_variable(temp_env, capsys):
    """Test unsetting a variable that doesn't exist"""
    unset('NONEXISTENT_VAR')
    captured = capsys.readouterr()
    assert 'not found' in captured.err.lower()

def test_unset_no_args(temp_env, capsys):
    """Test unset with no arguments"""
    unset()
    captured = capsys.readouterr()
    assert 'missing variable name' in captured.err.lower()

def test_export_path_handling(temp_env):
    """Test handling of PATH variable"""
    original_path = os.environ['PATH']
    new_path = '/usr/local/bin:/usr/bin'
    
    export(f'PATH={new_path}')
    assert os.environ['PATH'] == new_path
    
    # Test prepending to PATH
    export(f'PATH=/opt/bin:{os.environ["PATH"]}')
    assert os.environ['PATH'] == f'/opt/bin:{new_path}'
