#!/usr/bin/env python3

import os
import readline
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.builtins.history import history


@pytest.fixture
def setup_history():
    """Set up history for testing"""
    # Clear existing history
    readline.clear_history()
    
    # Add test entries
    test_commands = ["ls", "cd /tmp", "echo hello", "grep pattern file"]
    for cmd in test_commands:
        readline.add_history(cmd)
    
    yield
    
    # Clean up
    readline.clear_history()


def test_history_display(setup_history, capsys):
    """Test history display"""
    history()
    captured = capsys.readouterr()
    
    # Check that all entries are displayed
    assert "ls" in captured.out
    assert "cd /tmp" in captured.out
    assert "echo hello" in captured.out
    assert "grep pattern file" in captured.out
    
    # Check numbering
    lines = captured.out.strip().split('\n')
    assert len(lines) == readline.get_current_history_length()
    

def test_history_n_entries(setup_history, capsys):
    """Test displaying specific number of history entries"""
    history("2")
    captured = capsys.readouterr()
    
    # Should only show last 2 entries
    lines = captured.out.strip().split('\n')
    assert len(lines) == 2
    assert "echo hello" in captured.out
    assert "grep pattern file" in captured.out


def test_history_clear(setup_history, capsys):
    """Test clearing history"""
    assert readline.get_current_history_length() > 0
    
    # Use mock to avoid actual file operations
    with patch('os.remove'):
        history("-c")
    
    # Check that history is cleared
    assert readline.get_current_history_length() == 0


def test_history_delete_entry(setup_history, capsys):
    """Test deleting a history entry"""
    initial_len = readline.get_current_history_length()
    
    history("-d", "2")
    
    # Check that entry is deleted
    assert readline.get_current_history_length() == initial_len - 1
    
    # Make sure the entry is gone
    history()
    captured = capsys.readouterr()
    assert "cd /tmp" not in captured.out


def test_history_invalid_index(setup_history, capsys):
    """Test invalid index for deletion"""
    history("-d", "999")
    captured = capsys.readouterr()
    assert "invalid position" in captured.err.lower()


def test_history_invalid_number(setup_history, capsys):
    """Test invalid number of entries"""
    history("-1")  # Invalid negative number
    captured = capsys.readouterr()
    assert "invalid option" in captured.err.lower()


def test_history_invalid_command(setup_history, capsys):
    """Test history with invalid command"""
    history("-z")  # Invalid option
    captured = capsys.readouterr()
    assert "invalid option" in captured.err.lower()
    assert "usage" in captured.err.lower()
