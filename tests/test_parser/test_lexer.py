#!/usr/bin/env python3

import pytest
from src.parser.lexer import Token, tokenize, split_pipeline, parse_redirections

def test_basic_tokenization():
    """Test basic command tokenization"""
    line = "ls -l /tmp"
    tokens = tokenize(line)
    assert len(tokens) == 3
    assert [t.value for t in tokens] == ["ls", "-l", "/tmp"]
    assert all(t.type == 'word' for t in tokens)

def test_stderr_redirection():
    """Test stderr redirection tokenization"""
    # Basic stderr redirection
    tokens = tokenize("command 2> error.log")
    assert len(tokens) == 3
    assert tokens[1].value == "2>"
    assert tokens[1].type == "operator"
    assert tokens[2].value == "error.log"
    
    # Stderr append
    tokens = tokenize("command 2>> error.log")
    assert len(tokens) == 3
    assert tokens[1].value == "2>>"
    assert tokens[1].type == "operator"
    assert tokens[2].value == "error.log"
    
    # Multiple redirections
    tokens = tokenize("command > output.txt 2> error.log")
    assert len(tokens) == 5
    assert [t.value for t in tokens] == ["command", ">", "output.txt", "2>", "error.log"]
    
    # Stderr to stdout redirection
    tokens = tokenize("command 2>&1")
    assert len(tokens) == 3
    assert tokens[0].value == "command"
    assert tokens[1].value == "2>"
    assert tokens[2].value == "&1"

def test_redirection_parsing():
    """Test redirection parsing"""
    # Test stderr redirection
    tokens = tokenize("command 2> error.log")
    remaining, redirects = parse_redirections(tokens)
    assert len(remaining) == 1
    assert remaining[0].value == "command"
    assert len(redirects) == 1
    assert redirects[0] == ("2>", "error.log")
    
    # Test multiple redirections
    tokens = tokenize("command > output.txt 2> error.log")
    remaining, redirects = parse_redirections(tokens)
    assert len(remaining) == 1
    assert remaining[0].value == "command"
    assert len(redirects) == 2
    assert ("2>", "error.log") in redirects
    assert (">", "output.txt") in redirects

def test_command_substitution():
    """Test command substitution tokenization"""
    # $() substitution
    tokens = tokenize("echo $(date)")
    assert len(tokens) == 2
    assert tokens[0].value == "echo"
    assert tokens[1].value == "$(date)"
    
    # Backtick substitution - should preserve backticks as is
    tokens = tokenize("echo `date`")
    assert len(tokens) == 2
    assert tokens[0].value == "echo"
    assert tokens[1].value == "`date`"  # Keep backticks as is
    
    # Nested substitution
    tokens = tokenize("echo $(echo $(pwd))")
    assert len(tokens) == 2
    assert tokens[1].value == "$(echo $(pwd))"
    
    tokens = tokenize("echo `echo \\`pwd\\``")
    assert len(tokens) == 2
    assert tokens[1].value == "`echo \\`pwd\\``"  # Keep backticks as is
    
    # Substitution with arguments
    tokens = tokenize("echo $(ls -l)")
    assert len(tokens) == 2
    assert tokens[1].value == "$(ls -l)"
    
    tokens = tokenize("echo `ls -l`")
    assert len(tokens) == 2
    assert tokens[1].value == "`ls -l`"  # Keep backticks as is
    
    # Multiple substitutions
    tokens = tokenize("echo $(date) `pwd`")
    assert len(tokens) == 3
    assert tokens[1].value == "$(date)"
    assert tokens[2].value == "`pwd`"  # Keep backticks as is

def test_quoted_substitution():
    """Test command substitution in quotes"""
    # In double quotes
    tokens = tokenize('echo "Current date: $(date)"')
    assert len(tokens) == 2
    assert tokens[1].value == '"Current date: $(date)"'
    
    tokens = tokenize('echo "Current date: `date`"')
    assert len(tokens) == 2
    assert tokens[1].value == '"Current date: `date`"'  # Preserved in quotes
    
    # In single quotes (no substitution)
    tokens = tokenize("echo 'Output: $(date)'")
    assert len(tokens) == 2
    assert tokens[1].value == "'Output: $(date)'"
    
    tokens = tokenize("echo 'Output: `date`'")
    assert len(tokens) == 2
    assert tokens[1].value == "'Output: `date`'"

def test_substitution_with_operators():
    """Test command substitution with operators"""
    # With pipe
    tokens = tokenize("$(ls) | grep test")
    assert len(tokens) == 4
    assert tokens[0].value == "$(ls)"
    assert tokens[1].value == "|"
    
    # With redirection
    tokens = tokenize("$(date) > output.txt")
    assert len(tokens) == 3
    assert tokens[0].value == "$(date)"
    assert tokens[1].value == ">"

def test_invalid_substitution():
    """Test invalid command substitution syntax"""
    # Unclosed substitution
    with pytest.raises(ValueError, match="Unterminated command substitution"):
        tokenize("echo $(date")
    
    # Unclosed backtick
    tokens = tokenize("echo `date")
    assert len(tokens) == 2
    assert tokens[1].value == "`date"
    
    # Missing opening parenthesis
    tokens = tokenize("echo $date)")
    assert len(tokens) == 3
    assert tokens[1].value == "$"
    
    # Extra closing parenthesis
    tokens = tokenize("echo $(date))")
    assert len(tokens) == 3
    assert tokens[1].value == "$(date)"
    assert tokens[2].value == ")"
    
    # Escaped backticks
    tokens = tokenize("echo \\`date\\`")
    assert len(tokens) == 2
    assert tokens[1].value == "\\`date\\`"

def test_quoted_strings():
    """Test handling of quoted strings"""
    cases = [
        ('echo "hello world"', ['echo', '"hello world"']),
        ("echo 'single quotes'", ['echo', "'single quotes'"]),
        ('echo "nested \'quotes\'"', ['echo', '"nested \'quotes\'"']),
        ('echo "spaced     text"', ['echo', '"spaced     text"']),
    ]
    
    for input_line, expected in cases:
        tokens = tokenize(input_line)
        assert [t.value for t in tokens] == expected

def test_operators():
    """Test operator recognition"""
    line = "cmd1 | cmd2 > file 2>&1"
    tokens = tokenize(line)
    operators = [t for t in tokens if t.type == 'operator']
    assert len(operators) == 4
    assert [op.value for op in operators] == ["|", ">", "2>", "&1"]

def test_pipeline_splitting():
    """Test pipeline splitting"""
    tokens = tokenize("cmd1 arg1 | cmd2 arg2 | cmd3")
    segments = split_pipeline(tokens)
    assert len(segments) == 3
    assert [len(seg) for seg in segments] == [2, 2, 1]
    assert [seg[0].value for seg in segments] == ["cmd1", "cmd2", "cmd3"]

def test_redirections():
    """Test redirection parsing"""
    tokens = tokenize("cmd > output.txt 2> error.log < input.txt")
    remaining, redirects = parse_redirections(tokens)
    assert len(remaining) == 1
    assert remaining[0].value == "cmd"
    assert len(redirects) == 3
    assert (">" , "output.txt") in redirects
    assert ("2>", "error.log") in redirects
    assert ("<" , "input.txt") in redirects

def test_complex_command():
    """Test complex command parsing"""
    line = 'grep "test phrase" file.txt | sort -r > output.txt 2>&1'
    tokens = tokenize(line)
    segments = split_pipeline(tokens)
    
    # First segment
    cmd1_tokens, cmd1_redirs = parse_redirections(segments[0])
    assert [t.value for t in cmd1_tokens] == ['grep', '"test phrase"', 'file.txt']
    
    # Second segment
    cmd2_tokens, cmd2_redirs = parse_redirections(segments[1])
    assert [t.value for t in cmd2_tokens] == ['sort', '-r']
    assert ('>', 'output.txt') in cmd2_redirs
    assert ('2>&1', '1') in cmd2_redirs  # Now using the special form for 2>&1 redirection

def test_error_cases():
    """Test error handling"""
    with pytest.raises(ValueError):
        tokenize('echo "unclosed quote')
    
    with pytest.raises(ValueError):
        tokenize("echo 'nested \"quotes")
    
    with pytest.raises(ValueError):
        tokens = tokenize("cmd >")  # Missing redirection target
        parse_redirections(tokens)
