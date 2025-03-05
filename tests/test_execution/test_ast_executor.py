#!/usr/bin/env python3

import os
import tempfile
import pytest
from src.parser.ast import (
    CommandNode, PipelineNode, IfNode, WhileNode, 
    ForNode, CaseNode, ListNode, FunctionNode
)
from src.execution.ast_executor import ASTExecutor, Scope
from src.parser.parser import Parser


def test_scope_variables():
    scope = Scope()
    
    # Set a variable
    scope.set("test_var", "value")
    
    # Get the variable
    assert scope.get("test_var") == "value"
    
    # Nested scope inheritance
    child_scope = Scope(scope)
    assert child_scope.get("test_var") == "value"
    
    # Variable shadowing
    child_scope.set("test_var", "new_value")
    assert child_scope.get("test_var") == "new_value"
    assert scope.get("test_var") == "value"


def test_execute_command(capsys):
    executor = ASTExecutor()
    
    # Execute a simple echo command
    node = CommandNode("echo", ["echo", "hello", "world"])
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "hello world"


def test_execute_pipeline(capsys):
    executor = ASTExecutor()
    parser = Parser()
    
    # Parse and execute a pipeline
    node = parser.parse("echo hello | grep hello")
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "hello"


def test_execute_if_statement(capsys):
    executor = ASTExecutor()
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile() as temp_file:
        # Test with condition that evaluates to true
        condition = CommandNode("test", ["test", "-f", temp_file.name])
        then_branch = CommandNode("echo", ["echo", "file exists"])
        else_branch = CommandNode("echo", ["echo", "file does not exist"])
        
        node = IfNode(condition, then_branch, else_branch)
        result = executor.execute(node)
        
        assert result == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "file exists"
    
    # Test with condition that evaluates to false
    condition = CommandNode("test", ["test", "-f", "/nonexistent/file"])
    then_branch = CommandNode("echo", ["echo", "file exists"])
    else_branch = CommandNode("echo", ["echo", "file does not exist"])
    
    node = IfNode(condition, then_branch, else_branch)
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "file does not exist"


def test_execute_while_loop(capsys):
    executor = ASTExecutor()
    
    # Create a variable to track iterations
    executor.current_scope.set("counter", "0")
    
    # Create a condition that checks if counter < 3
    condition_cmd = """
    counter=$(($counter + 1))
    if [ $counter -le 3 ]; then
        exit 0
    else
        exit 1
    fi
    """
    
    # Use a shell command for the condition
    condition = CommandNode("sh", ["sh", "-c", condition_cmd])
    
    # Body just echoes the counter
    body = CommandNode("echo", ["echo", "Counter: $counter"])
    
    # Create while loop node
    node = WhileNode(condition, body)
    
    # Execute the loop
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    output_lines = captured.out.strip().split("\n")
    assert len(output_lines) == 3
    assert "Counter: 1" in output_lines[0]
    assert "Counter: 2" in output_lines[1]
    assert "Counter: 3" in output_lines[2]


def test_execute_for_loop(capsys):
    executor = ASTExecutor()
    
    # Create a for loop over some values
    variable = "item"
    words = ["apple", "banana", "cherry"]
    body = CommandNode("echo", ["echo", "Fruit: $item"])
    
    node = ForNode(variable, words, body)
    
    # Execute the loop
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    output_lines = captured.out.strip().split("\n")
    assert len(output_lines) == 3
    assert "Fruit: apple" in output_lines[0]
    assert "Fruit: banana" in output_lines[1]
    assert "Fruit: cherry" in output_lines[2]


def test_execute_case_statement(capsys):
    executor = ASTExecutor()
    
    # Set up variables
    executor.current_scope.set("fruit", "banana")
    
    # Create case items
    apple_action = CommandNode("echo", ["echo", "It's an apple"])
    banana_action = CommandNode("echo", ["echo", "It's a banana"])
    default_action = CommandNode("echo", ["echo", "Unknown fruit"])
    
    items = [
        src.parser.ast.CaseItem("apple", apple_action),
        src.parser.ast.CaseItem("banana", banana_action),
        src.parser.ast.CaseItem("*", default_action)
    ]
    
    # Create case node
    node = CaseNode("$fruit", items)
    
    # Execute the case statement
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "It's a banana"
    
    # Try with a different value
    executor.current_scope.set("fruit", "apple")
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "It's an apple"
    
    # Try with a value that doesn't match specific patterns
    executor.current_scope.set("fruit", "orange")
    result = executor.execute(node)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "Unknown fruit"


def test_execute_function(capsys):
    executor = ASTExecutor()
    
    # Define a function that echoes its arguments
    function_body = CommandNode("echo", ["echo", "Args: $1 $2"])
    function_node = FunctionNode("test_func", function_body)
    
    # Register the function
    result = executor.execute(function_node)
    assert result == 0
    
    # Create a call to the function
    function_call = CommandNode("test_func", ["test_func", "hello", "world"])
    
    # Execute the function call
    result = executor.execute(function_call)
    
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == "Args: hello world"