"""
Command parsing and lexical analysis

This module provides the parser for shell scripts, with a modern implementation
using grammar rules and better error handling.
"""

# Import directly from the state machine expander
from .state_machine_expander import StateMachineExpander

# Create a global instance for convenience
# Use os.environ.get directly instead of wrapping it in a lambda to ensure proper detection
import os
_global_expander = StateMachineExpander(scope_provider=os.environ.get, debug_mode=False)

# Re-export expander functions using the global instance
expand_variables = _global_expander.expand_variables
expand_all = _global_expander.expand_all  # Using the compatibility alias
expand_braces = _global_expander.expand_braces
expand_command_substitution = _global_expander.expand_command
expand_tilde = _global_expander.expand_tilde
expand_wildcards = _global_expander.expand_wildcards
expand_arithmetic = _global_expander.expand_arithmetic

from .quotes import handle_quotes, is_quoted, strip_quotes

# Import the new parser implementation
from .parser.shell_parser import ShellParser
from .token_types import Token, TokenType
from .lexer import tokenize
from .redirection import RedirectionParser

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
    'expand_all',
    'expand_braces',
    'expand_command_substitution',
    'expand_tilde',
    'expand_wildcards',
    'expand_arithmetic',
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
    'CaseItem',
    'StateMachineExpander'
]