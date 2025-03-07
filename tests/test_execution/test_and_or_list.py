#!/usr/bin/env python3
"""
Tests for AND-OR list execution in the shell.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import io

from src.parser.ast import AndOrNode, CommandNode
from src.execution.ast_executor import ASTExecutor


class TestAndOrList(unittest.TestCase):
    """Test cases for AND-OR list execution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.executor = ASTExecutor(interactive=False)
        
        # Mock command nodes
        self.true_command = CommandNode('true', ['true'], [])
        self.false_command = CommandNode('false', ['false'], [])
        self.echo_command = CommandNode('echo', ['echo', 'test'], [])
        
        # Patch execute to avoid actually running commands
        self.orig_execute = self.executor.execute
        
        def mock_execute(node):
            if node == self.true_command:
                return 0
            elif node == self.false_command:
                return 1
            elif node == self.echo_command:
                return 0
            return self.orig_execute(node)
            
        self.executor.execute = mock_execute
    
    def test_basic_and_operator(self):
        """Test basic AND operator."""
        # true && echo test - should execute both commands
        and_node = AndOrNode([(self.true_command, '&&'), (self.echo_command, None)])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(and_node)
            
        self.assertEqual(result, 0)
        
        # false && echo test - should only execute the first command
        and_node = AndOrNode([(self.false_command, '&&'), (self.echo_command, None)])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(and_node)
            
        self.assertEqual(result, 1)
    
    def test_basic_or_operator(self):
        """Test basic OR operator."""
        # false || echo test - should execute both commands
        or_node = AndOrNode([(self.false_command, '||'), (self.echo_command, None)])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(or_node)
            
        self.assertEqual(result, 0)
        
        # true || echo test - should only execute the first command
        or_node = AndOrNode([(self.true_command, '||'), (self.echo_command, None)])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(or_node)
            
        self.assertEqual(result, 0)
    
    def test_complex_chains(self):
        """Test more complex AND-OR chains."""
        # true && false && echo test - should execute the first two commands only
        chain = AndOrNode([
            (self.true_command, '&&'),
            (self.false_command, '&&'),
            (self.echo_command, None)
        ])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(chain)
            
        self.assertEqual(result, 1)
        
        # false || true && echo test - should execute all commands
        chain = AndOrNode([
            (self.false_command, '||'),
            (self.true_command, '&&'),
            (self.echo_command, None)
        ])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(chain)
            
        self.assertEqual(result, 0)
        
        # true || false && echo test - should only execute the first command
        chain = AndOrNode([
            (self.true_command, '||'),
            (self.false_command, '&&'),
            (self.echo_command, None)
        ])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(chain)
            
        self.assertEqual(result, 0)
    
    def test_exit_status_preservation(self):
        """Test that exit status is properly preserved."""
        # Create a more complex chain and verify exit status is returned correctly
        chain = AndOrNode([
            (self.true_command, '&&'),
            (self.echo_command, '&&'),
            (self.false_command, None)
        ])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(chain)
            
        self.assertEqual(result, 1)
        
        # Another chain with different exit status
        chain = AndOrNode([
            (self.false_command, '||'),
            (self.echo_command, None)
        ])
        
        with patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            result = self.executor.visit_and_or(chain)
            
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()