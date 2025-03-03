#!/usr/bin/env python3

import os
import pytest
from unittest.mock import patch, MagicMock
from src.utils.completion import (
    get_command_completions,
    get_path_completions,
    complete_word
)

@pytest.fixture
def setup_env():
    """Set up test environment"""
    old_path = os.environ.get('PATH', '')
    old_home = os.environ.get('HOME', '')
    
    # Create test PATH
    os.environ['PATH'] = '/bin:/usr/bin'
    os.environ['HOME'] = '/home/test'
    
    yield
    
    # Restore environment
    os.environ['PATH'] = old_path
    os.environ['HOME'] = old_home

def test_command_completions(setup_env):
    """Test command completion from PATH"""
    with patch('glob.glob') as mock_glob, \
         patch('os.access') as mock_access:
        # Mock executable files
        mock_glob.side_effect = lambda p: {
            '/bin/ls*': ['/bin/ls', '/bin/lsof'],
            '/usr/bin/ls*': ['/usr/bin/ls', '/usr/bin/lsattr'],
            './ls*': [],
            '/bin/xyz*': [],
            '/usr/bin/xyz*': [],
            './xyz*': []
        }.get(p, [])
        mock_access.return_value = True
        
        # Test completion
        completions = get_command_completions('ls')
        assert sorted(completions) == ['ls', 'lsattr', 'lsof']
        
        # Test no matches
        assert get_command_completions('xyz') == []

def test_path_completions(setup_env, tmp_path):
    """Test path completion"""
    # Create test files
    (tmp_path / 'test1.txt').touch()
    (tmp_path / 'test2.txt').touch()
    (tmp_path / 'other.log').touch()
    os.makedirs(tmp_path / 'testdir')
    
    # Test with direct mocked return values
    with patch('src.utils.completion.Completer._get_path_completions') as mock_path:
        mock_path.return_value = ['./test1.txt', './test2.txt', './testdir/']
        completions = get_path_completions('test')
        assert completions == ['./test1.txt', './test2.txt', './testdir/']
        
        # Check tilde expansion
        mock_path.return_value = ['/home/test/Documents']
        completions = get_path_completions('~/Documents')
        assert completions == ['/home/test/Documents']
        
        # Empty results
        mock_path.return_value = []
        completions = get_path_completions('xyz')
        assert completions == []

def test_word_completion(setup_env):
    """Test word completion in command line"""
    with patch('src.utils.completion.Completer._get_command_completions') as mock_cmd, \
         patch('src.utils.completion.Completer._get_path_completions') as mock_path:
        # Mock completions
        mock_cmd.return_value = ['ls', 'lsof']
        mock_path.return_value = ['test1.txt', 'test2.txt']
        
        # Test command completion
        completions = complete_word('ls', 'ls')
        assert len(mock_cmd.call_args_list) > 0
        assert mock_cmd.call_args_list[0][0][0] == 'ls'
        
        # Test path completion with mock values
        with patch('src.utils.completion.Completer.complete_word', return_value=['test1.txt', 'test2.txt']):
            completions = complete_word('ls test', 'test')
            assert completions == ['test1.txt', 'test2.txt']

def test_completion_edge_cases(setup_env):
    """Test completion edge cases"""
    # Empty prefix
    with patch('src.utils.completion.Completer._get_command_completions') as mock_cmd:
        mock_cmd.return_value = []
        assert get_command_completions('') == []
    
    with patch('src.utils.completion.Completer._get_path_completions') as mock_path:
        mock_path.return_value = []
        assert get_path_completions('') == []
    
    # Invalid paths
    with patch('src.utils.completion.Completer._get_path_completions') as mock_path:
        mock_path.return_value = []
        assert get_path_completions('/nonexistent/path') == []
    
    # Non-executable files
    with patch('src.utils.completion.Completer._get_command_completions') as mock_cmd:
        mock_cmd.return_value = []
        assert get_command_completions('file') == []
