"""
Command parsing and lexical analysis

This module provides the parser for shell scripts, with a modern implementation
using grammar rules and better error handling.
"""

# Import expander & quotes modules which are still supported here
from .expander import expand_variables, expand_command_substitution
from .quotes import handle_quotes, is_quoted, strip_quotes

# Import the new parser implementation
from .new.parser.shell_parser import ShellParser
from .new.token_types import Token, TokenType
from .new.lexer import tokenize
from .new.redirection import RedirectionParser

# Make RedirectionParser methods available at the module level for compatibility
parse_redirections = RedirectionParser.parse_redirections
split_pipeline = RedirectionParser.split_pipeline

# Re-export the AST nodes
from .ast import (
    Node, CommandNode, PipelineNode, IfNode, WhileNode, 
    ForNode, CaseNode, ListNode, FunctionNode, CaseItem
)

# Export the public API
__all__ = [
    'ShellParser',
    'Token',
    'TokenType',
    'tokenize',
    'parse_redirections',
    'split_pipeline',
    'expand_variables',
    'expand_command_substitution',
    'handle_quotes',
    'is_quoted',
    'strip_quotes',
    'Node',
    'CommandNode',
    'PipelineNode',
    'IfNode',
    'WhileNode',
    'ForNode',
    'CaseNode',
    'ListNode',
    'FunctionNode',
    'CaseItem'
]