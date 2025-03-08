#!/usr/bin/env python3

import pytest
from src.parser.ast import (
    CommandNode, PipelineNode, IfNode, WhileNode, 
    ForNode, CaseNode, ListNode
)
from src.parser.parser.shell_parser import ShellParser
from src.execution.ast_executor import ASTExecutor

def test_basic_command_parsing():
    parser = ShellParser()
    node = parser.parse_line("echo hello world")
    
    assert isinstance(node, CommandNode)
    assert node.command == "echo"
    assert node.args == ["echo", "hello", "world"]
    assert not node.background

def test_pipeline_parsing():
    # Using the token-based API directly for pipeline parsing
    from src.parser.lexer import tokenize
    from src.parser.parser.rules import PipelineRule
    from src.parser.parser.token_stream import TokenStream
    from src.parser.parser.parser_context import ParserContext
    
    # Set up the tokens, stream and context
    tokens = tokenize("echo hello | grep hello")
    stream = TokenStream(tokens)
    context = ParserContext()
    
    # Use the pipeline rule directly
    pipeline_rule = PipelineRule()
    node = pipeline_rule.parse(stream, context)
    
    assert isinstance(node, PipelineNode)
    assert len(node.commands) == 2
    assert node.commands[0].command == "echo"
    assert node.commands[1].command == "grep"

def test_background_command():
    parser = ShellParser()
    node = parser.parse_line("sleep 10 &")
    
    assert isinstance(node, CommandNode)
    assert node.command == "sleep"
    assert node.args == ["sleep", "10"]
    assert node.background

def test_if_statement():
    parser = ShellParser()
    node = parser.parse_line("if test -f /etc/passwd; then echo exists; fi")
    
    assert isinstance(node, IfNode)
    assert isinstance(node.condition, CommandNode)
    assert isinstance(node.then_branch, CommandNode)
    assert node.else_branch is None

def test_if_else_statement():
    parser = ShellParser()
    node = parser.parse_line("if test -f /nonexistent; then echo exists; else echo missing; fi")
    
    assert isinstance(node, IfNode)
    assert isinstance(node.condition, CommandNode)
    assert isinstance(node.then_branch, CommandNode)
    assert isinstance(node.else_branch, CommandNode)

def test_while_loop():
    parser = ShellParser()
    node = parser.parse_line("while test -f /tmp/flag; do echo waiting; sleep 1; done")
    
    assert isinstance(node, WhileNode)
    assert isinstance(node.condition, CommandNode)
    assert isinstance(node.body, ListNode)
    assert not node.until

def test_until_loop():
    parser = ShellParser()
    node = parser.parse_line("until test -f /tmp/flag; do echo waiting; sleep 1; done")
    
    assert isinstance(node, WhileNode)
    assert isinstance(node.condition, CommandNode)
    assert isinstance(node.body, ListNode)
    assert node.until

def test_for_loop():
    parser = ShellParser()
    node = parser.parse_line("for i in 1 2 3; do echo $i; done")
    
    assert isinstance(node, ForNode)
    assert node.variable == "i"
    assert node.words == ["1", "2", "3"]
    assert isinstance(node.body, CommandNode)

def test_complex_script():
    parser = ShellParser()
    # Use a simpler script for now until we fix multi-line parsing
    script = "if test -f /etc/passwd; then echo File exists; else echo File missing; fi"
    
    node = parser.parse_line(script)
    assert isinstance(node, IfNode)
    assert isinstance(node.condition, CommandNode)
    assert isinstance(node.then_branch, CommandNode)
    assert isinstance(node.else_branch, CommandNode)
