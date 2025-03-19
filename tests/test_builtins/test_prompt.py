#!/usr/bin/env python3

import pytest
import os
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch, MagicMock

from src.builtins.core import prompt
from src.config.manager import ConfigManager
from src.utils.prompt import PromptFormatter


class TestPromptBuiltin:
    """Tests for the prompt builtin command"""

    def setup_method(self):
        """Set up test environment"""
        # Create a mock config manager
        self.mock_config_manager = ConfigManager()
        # Store original prompt template
        self.original_template = self.mock_config_manager.get('prompt_template')
        
    def teardown_method(self):
        """Clean up after tests"""
        # Restore original prompt template
        if hasattr(self, 'original_template'):
            self.mock_config_manager.set('prompt_template', self.original_template)

    @patch('src.context.SHELL')
    def test_prompt_no_args(self, mock_shell):
        """Test prompt command with no arguments"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        
        # Create a test template
        test_template = "test_template"
        self.mock_config_manager.set('prompt_template', test_template)
        
        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = prompt()
        
        # Verify
        assert result == 0
        assert f"Current prompt template: {test_template}" in captured_output.getvalue()

    @patch('src.context.SHELL')
    def test_prompt_help(self, mock_shell):
        """Test prompt command with -h argument"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        
        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = prompt("-h")
        
        # Verify
        assert result == 0
        assert "Prompt Variables:" in captured_output.getvalue()
        assert "\\u - Username" in captured_output.getvalue()
        assert "\\w - Current working directory" in captured_output.getvalue()

    @patch('src.context.SHELL')
    def test_prompt_list(self, mock_shell):
        """Test prompt command with -l argument"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        
        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = prompt("-l")
        
        # Verify
        assert result == 0
        assert "Predefined prompts:" in captured_output.getvalue()
        assert "default" in captured_output.getvalue()
        assert "minimal" in captured_output.getvalue()

    @patch('src.context.SHELL')
    def test_prompt_set_predefined(self, mock_shell):
        """Test setting prompt to a predefined template"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        
        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = prompt("minimal")
        
        # Verify
        assert result == 0
        assert "Prompt set to:" in captured_output.getvalue()
        assert self.mock_config_manager.get('prompt_template') == "\\$ "

    @patch('src.context.SHELL')
    def test_prompt_set_custom(self, mock_shell):
        """Test setting prompt to a custom template"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        custom_template = "\\w > "
        
        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = prompt(custom_template)
        
        # Verify
        assert result == 0
        assert "Prompt set to:" in captured_output.getvalue()
        assert self.mock_config_manager.get('prompt_template') == custom_template
        
    @patch('src.context.SHELL')
    def test_prompt_set_unescaped(self, mock_shell):
        """Test setting prompt with unescaped variables (command line style)"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        # Simulate input as it would come from the command line - unescaped
        unescaped_template = "u:w:g$ "
        
        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = prompt(unescaped_template)
        
        # Verify
        assert result == 0
        assert "Prompt set to:" in captured_output.getvalue()
        # Should be converted to properly escaped form
        expected_template = "\\u:\\w:\\g\\$ "
        assert self.mock_config_manager.get('prompt_template') == expected_template

    @patch('src.context.SHELL')
    def test_prompt_error_no_shell(self, mock_shell):
        """Test prompt command when no shell instance is available"""
        # Setup
        mock_shell.get_current_shell.return_value = None
        
        # Capture stderr
        captured_error = io.StringIO()
        with redirect_stderr(captured_error):
            result = prompt()
        
        # Verify
        assert result == 1
        assert "prompt: no active shell instance" in captured_error.getvalue()

    @patch('src.context.SHELL')
    @patch('src.utils.prompt.PromptFormatter.format')
    def test_prompt_error_formatting(self, mock_format, mock_shell):
        """Test error handling when formatting fails"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        mock_format.side_effect = Exception("Test formatting error")
        
        # Capture stderr
        captured_error = io.StringIO()
        with redirect_stderr(captured_error):
            result = prompt("bad\\template")
        
        # Verify
        assert result == 1
        assert "prompt: error setting prompt" in captured_error.getvalue()

    @patch('src.context.SHELL')
    def test_prompt_integration(self, mock_shell):
        """Integration test to verify prompt is properly updated and formatted"""
        # Setup
        mock_shell._config_manager = self.mock_config_manager
        mock_shell.get_current_shell.return_value = "dummy_shell"
        
        # Set a simple prompt template
        test_template = "TEST-\\w-$ "
        
        # Run prompt command
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            result = prompt(test_template)
        
        # Verify prompt template was set
        assert result == 0
        assert self.mock_config_manager.get('prompt_template') == test_template
        
        # Verify formatted output was generated
        # We expect the prompt to contain the working directory
        assert "TEST-" in captured_output.getvalue()
        assert "-$ " in captured_output.getvalue()