#!/usr/bin/env python3
"""
POSIX-compatible test command implementation for psh.
Supports test and [ commands with standard file, string and integer tests.
"""

import os
import sys
from typing import List, Optional, Tuple, Any

def test_command(*args: str) -> int:
    """
    POSIX test command implementation.
    
    Usage:
        test EXPRESSION
        [ EXPRESSION ]
        
    Evaluates conditional expressions with file tests, string tests,
    integer comparisons and logical operators.
    
    Returns:
        0 if expression evaluates to true
        1 if expression evaluates to false
        2 if an error occurs
    """
    # Convert args tuple to list for easier manipulation
    args_list = list(args)
    
    # Determine command name from invocation
    command_name = "test"
    
    # Check if called as [
    if args_list and args_list[0] == '[':
        command_name = "["
        # Remove the [ from the beginning
        args_list.pop(0)
        
        # Check for closing bracket
        if not args_list or args_list[-1] != ']':
            print("[: missing ']'", file=sys.stderr)
            return 2
        # Remove the closing bracket
        args_list.pop()
    
    # Handle empty expression
    if not args_list:
        return 1  # False when no arguments
    
    # Parse and evaluate the expression
    try:
        result = _evaluate_expression(args_list)
        return 0 if result else 1
    except ValueError as e:
        print(f"{command_name}: {str(e)}", file=sys.stderr)
        return 2

def _evaluate_expression(args: List[str]) -> bool:
    """
    Evaluate a test expression with proper operator precedence.
    Implements a recursive descent parser for test expressions.
    """
    if not args:
        return False
    
    # Special case for single argument (non-empty string test)
    if len(args) == 1:
        return bool(args[0])
    
    # Handle grouping with parentheses
    if _is_grouped_expression(args):
        # Remove outer parentheses and evaluate inner expression
        return _evaluate_expression(args[1:-1])
    
    # Handle negation (highest precedence unary operator)
    if args[0] == '!':
        return not _evaluate_expression(args[1:])
    
    # Look for binary logical operators (in precedence order)
    # OR has lowest precedence
    or_index = _find_operator(args, '-o')
    if or_index >= 0:
        left = _evaluate_expression(args[:or_index])
        # Short-circuit evaluation
        if left:
            return True
        right = _evaluate_expression(args[or_index+1:])
        return right
    
    # AND has higher precedence than OR
    and_index = _find_operator(args, '-a')
    if and_index >= 0:
        left = _evaluate_expression(args[:and_index])
        # Short-circuit evaluation
        if not left:
            return False
        right = _evaluate_expression(args[and_index+1:])
        return right
    
    # Handle binary operators
    if len(args) == 3:
        return _evaluate_binary_operator(args[0], args[1], args[2])
    
    # Handle unary operators
    if len(args) == 2:
        return _evaluate_unary_operator(args[0], args[1])
    
    # If we get here, it's an invalid expression
    raise ValueError(f"invalid test expression: {' '.join(args)}")

def _is_grouped_expression(args: List[str]) -> bool:
    """Check if an expression is enclosed in parentheses."""
    if not args or len(args) < 2:
        return False
    
    if args[0] != '(' or args[-1] != ')':
        return False
    
    # Check for balanced parentheses to ensure we're not
    # capturing a partial expression
    depth = 0
    for i, arg in enumerate(args):
        if arg == '(':
            depth += 1
        elif arg == ')':
            depth -= 1
            # If depth becomes 0 before the last token, this isn't
            # an enclosing parenthesis but part of a nested expression
            if depth == 0 and i != len(args) - 1:
                return False
    
    return depth == 0

def _find_operator(args: List[str], op: str) -> int:
    """
    Find an operator at the top level of the expression.
    Skips operators within parenthesized groups.
    """
    depth = 0
    for i, arg in enumerate(args):
        if arg == '(':
            depth += 1
        elif arg == ')':
            depth -= 1
        elif arg == op and depth == 0:
            return i
    return -1

def _evaluate_binary_operator(left: str, op: str, right: str) -> bool:
    """Evaluate a binary operator expression."""
    # String comparison operators
    if op == '=':
        return left == right
    elif op == '!=':
        return left != right
    
    # Integer comparison operators
    elif op in ['-eq', '-ne', '-gt', '-ge', '-lt', '-le']:
        try:
            left_val = int(left)
            right_val = int(right)
        except ValueError:
            raise ValueError(f"integer expression expected: {left} or {right}")
        
        if op == '-eq':
            return left_val == right_val
        elif op == '-ne':
            return left_val != right_val
        elif op == '-gt':
            return left_val > right_val
        elif op == '-ge':
            return left_val >= right_val
        elif op == '-lt':
            return left_val < right_val
        elif op == '-le':
            return left_val <= right_val
    
    raise ValueError(f"unknown binary operator: {op}")

def _evaluate_unary_operator(op: str, arg: str) -> bool:
    """Evaluate a unary operator expression."""
    # String tests
    if op == '-z':
        return len(arg) == 0
    elif op == '-n':
        return len(arg) > 0
    
    # File tests
    elif op == '-e':
        return os.path.exists(arg)
    elif op == '-f':
        return os.path.isfile(arg)
    elif op == '-d':
        return os.path.isdir(arg)
    elif op == '-r':
        return os.access(arg, os.R_OK)
    elif op == '-w':
        return os.access(arg, os.W_OK)
    elif op == '-x':
        return os.access(arg, os.X_OK)
    elif op == '-s':
        return os.path.exists(arg) and os.path.getsize(arg) > 0
    elif op == '-L':
        return os.path.islink(arg)
    
    raise ValueError(f"unknown unary operator: {op}")