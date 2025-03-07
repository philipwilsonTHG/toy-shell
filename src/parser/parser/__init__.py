"""
New parser module for the shell.

This module provides a modular and extensible parser implementation
for shell scripts, with better error handling and maintainability.
"""

from .token_stream import TokenStream, Position
from .parser_context import ParserContext
from .grammar_rule import GrammarRule
from .shell_parser import ShellParser
from .rules import (
    CommandRule,
    PipelineRule,
    IfStatementRule,
    WhileStatementRule,
    ForStatementRule,
    CaseStatementRule,
    FunctionDefinitionRule
)

# Function for external use
def parse(tokens):
    """Parse a list of tokens into an AST."""
    parser = ShellParser()
    return parser.parse(tokens)

__all__ = [
    'TokenStream',
    'Position',
    'ParserContext',
    'GrammarRule',
    'ShellParser',
    'CommandRule',
    'PipelineRule',
    'IfStatementRule',
    'WhileStatementRule',
    'ForStatementRule',
    'CaseStatementRule',
    'FunctionDefinitionRule',
    'parse'
]