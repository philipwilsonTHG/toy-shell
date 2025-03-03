#!/usr/bin/env python3

import os
import sys
import tempfile
import pytest
from pathlib import Path

from src.builtins.core import source


def test_source_missing_file(capfd):
    """Test source command with missing file"""
    result = source("nonexistent_file")
    captured = capfd.readouterr()
    
    assert result > 0  # Should return non-zero exit code
    assert "No such file" in captured.err


def test_source_no_filename(capfd):
    """Test source command with no filename"""
    result = source()
    captured = capfd.readouterr()
    
    assert result > 0  # Should return non-zero exit code
    assert "filename argument required" in captured.err


def test_source_basic_commands(tmp_path, capfd):
    """Test source command with basic commands"""
    # Create a test script
    script_path = tmp_path / "test_script.sh"
    script_path.write_text("echo 'Hello from script'\necho 'Second line'")
    
    result = source(str(script_path))
    captured = capfd.readouterr()
    
    assert "Hello from script" in captured.out
    assert "Second line" in captured.out


def test_source_comments_and_empty_lines(tmp_path, capfd):
    """Test source command with comments and empty lines"""
    # Create a test script with comments and empty lines
    script_path = tmp_path / "comment_script.sh"
    script_path.write_text("""# This is a comment
echo 'First command'

# Another comment
echo 'Second command'

""")
    
    result = source(str(script_path))
    captured = capfd.readouterr()
    
    assert "First command" in captured.out
    assert "Second command" in captured.out
    assert "# This is a comment" not in captured.out