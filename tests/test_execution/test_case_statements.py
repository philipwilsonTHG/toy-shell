#!/usr/bin/env python3
"""
Test case statement parsing and execution.
"""

from unittest.mock import patch

from src.execution.ast_executor import ASTExecutor
from src.parser.ast import CaseNode, CaseItem, CommandNode


class TestCaseStatements:
    """Test case statement execution."""

    def test_pattern_match_simple(self):
        """Test simple pattern matching."""
        executor = ASTExecutor()

        # Simple equality matching
        assert executor.pattern_match("apple", "apple") is True
        assert executor.pattern_match("apple", "orange") is False

        # Wildcard matching
        assert executor.pattern_match("apple", "*") is True
        assert executor.pattern_match("apple.txt", "*.txt") is True
        assert executor.pattern_match("apple.jpg", "*.txt") is False

        # Alternative patterns with |
        assert executor.pattern_match("apple", "apple|orange") is True
        assert executor.pattern_match("orange", "apple|orange") is True
        assert executor.pattern_match("banana", "apple|orange") is False
        assert executor.pattern_match("document.txt", "*.jpg|*.png|*.txt") is True
        assert executor.pattern_match("photo.png", "*.jpg|*.png|*.txt") is True
        assert executor.pattern_match("code.py", "*.jpg|*.png|*.txt") is False

    def test_execute_case_statement_single_pattern(self):
        """Test case statement with single pattern."""
        executor = ASTExecutor()

        # Create case items
        apple_action = CommandNode("echo", ["echo", "It's an apple"])
        orange_action = CommandNode("echo", ["echo", "It's an orange"])
        default_action = CommandNode("echo", ["echo", "Unknown fruit"])

        items = [
            CaseItem("apple", apple_action),
            CaseItem("orange", orange_action),
            CaseItem("*", default_action)
        ]

        # Create case node with word that should match the first pattern
        node = CaseNode("apple", items)

        # Mock the word expander to return the same value (no actual expansion needed)
        with patch.object(executor.word_expander, 'expand', side_effect=lambda x: x):
            # Execute the case statement
            result = executor.visit_case(node)

            # It should return 0 (success) and execute the apple action
            assert result == 0

    def test_execute_case_statement_multiple_patterns(self):
        """Test case statement with pattern alternatives using |."""
        executor = ASTExecutor()

        # Create case items with pattern alternatives
        common_fruit_action = CommandNode("echo", ["echo", "It's a common fruit"])
        exotic_fruit_action = CommandNode("echo", ["echo", "It's an exotic fruit"])
        default_action = CommandNode("echo", ["echo", "Mystery fruit"])

        items = [
            CaseItem("apple|banana|cherry", common_fruit_action),
            CaseItem("kiwi|dragon*|star*", exotic_fruit_action),
            CaseItem("*", default_action)
        ]

        # Test with banana (should match first pattern)
        node1 = CaseNode("banana", items)

        # Test with dragonfruit (should match second pattern)
        node2 = CaseNode("dragonfruit", items)

        # Test with kumquat (should match default pattern)
        node3 = CaseNode("kumquat", items)

        # Mock the word expander and executor methods
        with patch.object(executor.word_expander, 'expand', side_effect=lambda x: x), \
             patch.object(executor, 'execute', return_value=0) as mock_exec:

            # Execute node1
            result1 = executor.visit_case(node1)
            assert result1 == 0
            assert mock_exec.call_count == 1
            assert mock_exec.call_args[0][0] == common_fruit_action

            mock_exec.reset_mock()

            # Execute node2
            result2 = executor.visit_case(node2)
            assert result2 == 0
            assert mock_exec.call_count == 1
            assert mock_exec.call_args[0][0] == exotic_fruit_action

            mock_exec.reset_mock()

            # Execute node3
            result3 = executor.visit_case(node3)
            assert result3 == 0
            assert mock_exec.call_count == 1
            assert mock_exec.call_args[0][0] == default_action

    def test_execute_case_statement_with_glob_patterns(self):
        """Test case statement with glob patterns."""
        executor = ASTExecutor()

        # Create case items with glob patterns
        text_file_action = CommandNode("echo", ["echo", "It's a text file"])
        image_file_action = CommandNode("echo", ["echo", "It's an image file"])
        default_action = CommandNode("echo", ["echo", "Unknown file type"])

        items = [
            CaseItem("*.txt", text_file_action),
            CaseItem("*.jpg|*.png|*.gif", image_file_action),
            CaseItem("*", default_action)
        ]

        # Test with document.txt (should match first pattern)
        node1 = CaseNode("document.txt", items)

        # Test with photo.jpg (should match second pattern)
        node2 = CaseNode("photo.jpg", items)

        # Test with code.py (should match default pattern)
        node3 = CaseNode("code.py", items)

        # Mock the word expander and executor methods
        with patch.object(executor.word_expander, 'expand', side_effect=lambda x: x), \
             patch.object(executor, 'execute', return_value=0) as mock_exec:

            # Execute node1
            result1 = executor.visit_case(node1)
            assert result1 == 0
            assert mock_exec.call_count == 1
            assert mock_exec.call_args[0][0] == text_file_action

            mock_exec.reset_mock()

            # Execute node2
            result2 = executor.visit_case(node2)
            assert result2 == 0
            assert mock_exec.call_count == 1
            assert mock_exec.call_args[0][0] == image_file_action

            mock_exec.reset_mock()

            # Execute node3
            result3 = executor.visit_case(node3)
            assert result3 == 0
            assert mock_exec.call_count == 1
            assert mock_exec.call_args[0][0] == default_action
