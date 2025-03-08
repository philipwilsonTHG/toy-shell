#!/usr/bin/env python3

import os
import re
import sys
import glob
import fnmatch
from typing import Dict, List, Optional, Any, Tuple, Callable

from ..parser.ast import (
    ASTVisitor, Node, CommandNode, PipelineNode, IfNode, WhileNode,
    ForNode, CaseNode, FunctionNode, ListNode, CaseItem, AndOrNode
)
from ..execution.pipeline import PipelineExecutor
from ..context import SHELL
from ..parser.expander import expand_all, expand_braces
from ..parser.token_types import Token, TokenType, create_word_token


class ExecutionError(Exception):
    """Exception raised during AST execution"""
    pass


class FunctionRegistry:
    """Registry for shell functions"""
    
    def __init__(self):
        self.functions: Dict[str, FunctionNode] = {}
    
    def register(self, name: str, node: FunctionNode):
        """Register a function definition"""
        self.functions[name] = node
    
    def get(self, name: str) -> Optional[FunctionNode]:
        """Get a function definition by name"""
        return self.functions.get(name)
    
    def exists(self, name: str) -> bool:
        """Check if a function exists"""
        return name in self.functions


class Scope:
    """Variable scope for shell execution"""
    
    def __init__(self, parent: Optional['Scope'] = None):
        self.variables: Dict[str, str] = {}
        self.parent = parent
    
    def get(self, name: str) -> Optional[str]:
        """Get a variable value, checking parent scopes"""
        if name in self.variables:
            return self.variables[name]
        
        if self.parent:
            return self.parent.get(name)
        
        # Fall back to environment variables
        return os.environ.get(name)
    
    def set(self, name: str, value: str):
        """Set a variable in the current scope"""
        self.variables[name] = value
    
    def export(self, name: str):
        """Export a variable to the environment"""
        if name in self.variables:
            os.environ[name] = self.variables[name]


class ASTExecutor(ASTVisitor):
    """Executes AST nodes using visitor pattern"""
    
    def __init__(self, interactive: bool = True, debug_mode: bool = False):
        self.interactive = interactive
        self.debug_mode = debug_mode
        self.pipeline_executor = PipelineExecutor(interactive)
        self.exit_status = 0
        self.last_status = 0
        self.function_registry = FunctionRegistry()
        self.global_scope = Scope()
        self.current_scope = self.global_scope
    
    def execute(self, node: Node) -> int:
        """Execute an AST node"""
        if node is None:
            return 0
        
        # Print AST in debug mode
        if self.debug_mode:
            print("[DEBUG] Executing AST:", file=sys.stderr)
            self._print_ast(node)
            
        result = node.accept(self)
        
        # Some visitor methods return None, use last_status in those cases
        if result is None:
            return self.last_status
            
        return result
    
    def _print_ast(self, node: Node, indent: int = 0):
        """Print an AST node with indentation for debugging"""
        prefix = "  " * indent
        if node is None:
            print(f"{prefix}None", file=sys.stderr)
            return
            
        # Print node representation
        node_str = repr(node)
        print(f"{prefix}{node_str}", file=sys.stderr)
        
        # Recursively print child nodes
        if isinstance(node, ListNode):
            for child in node.nodes:
                self._print_ast(child, indent + 1)
        elif isinstance(node, IfNode):
            print(f"{prefix}  Condition:", file=sys.stderr)
            self._print_ast(node.condition, indent + 2)
            print(f"{prefix}  Then branch:", file=sys.stderr)
            self._print_ast(node.then_branch, indent + 2)
            if node.else_branch:
                print(f"{prefix}  Else branch:", file=sys.stderr)
                self._print_ast(node.else_branch, indent + 2)
        elif isinstance(node, WhileNode):
            print(f"{prefix}  Condition:", file=sys.stderr)
            self._print_ast(node.condition, indent + 2)
            print(f"{prefix}  Body:", file=sys.stderr)
            self._print_ast(node.body, indent + 2)
        elif isinstance(node, ForNode):
            print(f"{prefix}  Variable: {node.variable}", file=sys.stderr)
            print(f"{prefix}  Words: {node.words}", file=sys.stderr)
            print(f"{prefix}  Body:", file=sys.stderr)
            self._print_ast(node.body, indent + 2)
        elif isinstance(node, CaseNode):
            for i, item in enumerate(node.items):
                print(f"{prefix}  Pattern {i+1} ({item.pattern}):", file=sys.stderr)
                self._print_ast(item.action, indent + 2)
        elif isinstance(node, FunctionNode):
            print(f"{prefix}  Body:", file=sys.stderr)
            self._print_ast(node.body, indent + 2)
    
    def visit_command(self, node: CommandNode) -> int:
        """Execute a simple command"""
        if not node.command:
            return 0
            
        # Check if this is a function call
        if self.function_registry.exists(node.command):
            func_node = self.function_registry.get(node.command)
            
            # Create new scope for function execution
            old_scope = self.current_scope
            self.current_scope = Scope(old_scope)
            
            # Set positional parameters as variables
            for i, arg in enumerate(node.args[1:], 1):
                self.current_scope.set(str(i), arg)
            
            # Execute function body
            result = self.execute(func_node.body)
            
            # Restore previous scope
            self.current_scope = old_scope
            
            return result
            
        # Special handling for variable assignments (VAR=value command)
        assignment_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)', node.command)
        if assignment_match and not node.args[1:]:
            var_name = assignment_match.group(1)
            var_value = assignment_match.group(2)
            
            # Strip quotes if present
            if (var_value.startswith('"') and var_value.endswith('"')) or \
               (var_value.startswith("'") and var_value.endswith("'")):
                var_value = var_value[1:-1]
                
            self.current_scope.set(var_name, var_value)
            return 0
            
        # Handle builtin command 'test' or '['
        if node.command in ['test', '[']:
            try:
                return self.handle_test_command(node.args)
            except ExecutionError as e:
                # Print error to stderr
                print(f"Error: {e}", file=sys.stderr)
                return 1
        
        # Regular command execution using pipeline executor
        # Process the command, arguments, and redirections to get tokens
        tokens = self._process_command_to_tokens(node.command, node.args, node.redirections)
            
        # Execute the command
        result = self.pipeline_executor.execute_pipeline(tokens, node.background)
        self.last_status = result if result is not None else 0
        return self.last_status
        
    def _process_command_to_tokens(self, command: str, args: List[str], 
                                redirections: List[Tuple[str, str]]) -> List[Token]:
        """
        Convert a command, its args, and redirections to tokens with expansion
        
        Args:
            command: The command to execute
            args: List of command arguments (first item is the command itself)
            redirections: List of redirection tuples (operator, target)
            
        Returns:
            List of tokens ready for pipeline execution
        """
        tokens = []
        
        # Handle command expansion
        fixed_command = self._handle_escaped_dollars(command)
        expanded_command = self.expand_word(fixed_command)
        
        # Handle brace expansion in the command itself
        if ' ' in expanded_command:
            # Split into multiple tokens - first one is the command, rest are args
            words = expanded_command.split()
            tokens.append(create_word_token(words[0]))
            for word in words[1:]:
                tokens.append(create_word_token(word))
        else:
            tokens.append(create_word_token(expanded_command))
        
        # Handle arguments (skip the first one which is the command itself)
        for arg in args[1:]:
            # Check if we need to preserve spaces for quotes
            is_quoted_arg = (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'"))
            
            # First handle escaped dollar signs, converting \$ to $ prior to expansion
            fixed_arg = self._handle_escaped_dollars(arg)
            
            # Expand the argument
            expanded_arg = self.expand_word(fixed_arg)
            
            # For debugging
            if self.debug_mode:
                print(f"[DEBUG] Processing arg: '{arg}' => '{expanded_arg}' (quoted: {is_quoted_arg})", file=sys.stderr)
            
            # Handle brace expansion results - may contain spaces that need word splitting
            if ' ' in expanded_arg and not is_quoted_arg:
                # Split the expanded result into multiple tokens
                for word in expanded_arg.split():
                    if self.debug_mode:
                        print(f"[DEBUG] Word splitting: '{expanded_arg}' -> '{word}'", file=sys.stderr)
                    tokens.append(create_word_token(word, quoted=False))
            else:
                # Create a special token attribute to mark quoted arguments
                token = create_word_token(expanded_arg, quoted=is_quoted_arg)
                tokens.append(token)
        
        # Handle redirections
        for redir_op, redir_target in redirections:
            # Special handling for 2>&1 format
            if redir_op == '2>&1':
                # This is already in the format we want
                tokens.append(Token('2>', TokenType.OPERATOR))
                tokens.append(Token('&1', TokenType.OPERATOR))
            elif redir_op == '2>' and redir_target == '&1':
                # Also handle this format explicitly
                tokens.append(Token('2>', TokenType.OPERATOR))
                tokens.append(Token('&1', TokenType.OPERATOR))
            else:
                tokens.append(Token(redir_op, TokenType.OPERATOR))
                fixed_target = self._handle_escaped_dollars(redir_target)
                expanded_target = self.expand_word(fixed_target)
                tokens.append(create_word_token(expanded_target))
                
        return tokens
        
    def _handle_escaped_dollars(self, text: str) -> str:
        """
        Handle escaped dollar signs, converting escaped $ to $ for variable substitution
        
        Args:
            text: The text to process
        
        Returns:
            The text with escaped dollars converted
        """
        # Check for backslash-dollar sequences
        if '\\$' in text:
            return text.replace('\\$', '$')
        return text
    
    def visit_pipeline(self, node: PipelineNode) -> int:
        """Execute a pipeline of commands"""
        # Convert back to tokens for pipeline executor
        tokens = []
        
        # Process each command in the pipeline
        for i, cmd in enumerate(node.commands):
            # Process each command to tokens
            cmd_tokens = self._process_command_to_tokens(cmd.command, cmd.args, cmd.redirections)
            tokens.extend(cmd_tokens)
            
            # Add pipe between commands (except after the last command)
            if i < len(node.commands) - 1:
                tokens.append(Token('|', TokenType.OPERATOR))
        
        # Execute the pipeline
        result = self.pipeline_executor.execute_pipeline(tokens, node.background)
        self.last_status = result if result is not None else 0
        return self.last_status
    
    def visit_if(self, node: IfNode) -> int:
        """Execute an if statement"""
        # Execute condition
        condition_status = self.execute(node.condition)
        self.last_status = condition_status
        
        if condition_status == 0:
            # Condition is true (exit status 0)
            return self.execute(node.then_branch)
        elif node.else_branch:
            # Condition is false, execute else branch if it exists
            return self.execute(node.else_branch)
        
        return condition_status
    
    def visit_while(self, node: WhileNode) -> int:
        """Execute a while or until loop"""
        result = 0
        condition_result = self.execute(node.condition)
        
        # For while loops, continue if condition is true (exit code 0)
        # For until loops, continue if condition is false (exit code non-zero)
        keep_looping = (not node.until and condition_result == 0) or \
                       (node.until and condition_result != 0)
                       
        while keep_looping:
            # Execute the body
            result = self.execute(node.body)
            self.last_status = result
            
            # Check condition for next iteration
            condition_result = self.execute(node.condition)
            keep_looping = (not node.until and condition_result == 0) or \
                           (node.until and condition_result != 0)
        
        return result
    
    def visit_for(self, node: ForNode) -> int:
        """Execute a for loop"""
        result = 0
        
        # Expand any globs in the words
        expanded_words = []
        for word in node.words:
            # First expand variables in the word
            expanded_word = self.expand_word(word)
            
            # Then handle globs
            if any(c in expanded_word for c in '*?['):
                matches = glob.glob(expanded_word)
                if matches:
                    expanded_words.extend(matches)
                else:
                    expanded_words.append(expanded_word)
            else:
                expanded_words.append(expanded_word)
        
        # Execute once for each word
        for word in expanded_words:
            # Set loop variable in current scope
            self.current_scope.set(node.variable, word)
            
            # For debugging
            if self.debug_mode:
                print(f"[DEBUG] For loop iteration with {node.variable}={word}", file=sys.stderr)
            
            # Execute the loop body without deepcopy - the variable expansion
            # will happen properly through the scope system now
            result = self.execute(node.body)
            self.last_status = result
        
        return result
    
    def visit_case(self, node: CaseNode) -> int:
        """Execute a case statement"""
        # Expand the word
        word = self.expand_word(node.word)
        
        # Check each pattern
        for item in node.items:
            pattern = self.expand_word(item.pattern)
            
            # Match pattern against word
            if self.pattern_match(word, pattern):
                # Execute matching action
                result = self.execute(item.action)
                self.last_status = result
                return result
        
        # No patterns matched
        return 0
    
    def visit_function(self, node: FunctionNode) -> int:
        """Define a function"""
        self.function_registry.register(node.name, node)
        return 0
        
    def visit_and_or(self, node: AndOrNode) -> int:
        """
        Execute an AND-OR list with proper short-circuit evaluation.
        
        For AND (&&) operations:
            - If the left command succeeds (exit status 0), execute the right command
            - If the left command fails (non-zero exit status), skip the right command
            
        For OR (||) operations:
            - If the left command succeeds (exit status 0), skip the right command
            - If the left command fails (non-zero exit status), execute the right command
            
        Returns the exit status of the last executed command.
        """
        result = 0
        
        # Debug output
        if self.debug_mode:
            print("[DEBUG] Executing AND-OR list:", file=sys.stderr)
            for i, (cmd, op) in enumerate(node.commands_with_operators):
                op_str = f" {op} " if op else ""
                print(f"  {i}: {cmd}{op_str}", file=sys.stderr)
        
        # Execute commands with short-circuit evaluation
        for command_node, operator in node.commands_with_operators:
            # Execute the current command
            result = self.execute(command_node)
            self.last_status = result
            
            # Handle short-circuit logic based on the operator
            if operator == '&&' and result != 0:
                # AND operation: if the left command fails, short-circuit and skip the rest
                if self.debug_mode:
                    print(f"[DEBUG] Short-circuit AND: Command failed with status {result}", file=sys.stderr)
                break
            elif operator == '||' and result == 0:
                # OR operation: if the left command succeeds, short-circuit and skip the rest
                if self.debug_mode:
                    print(f"[DEBUG] Short-circuit OR: Command succeeded with status {result}", file=sys.stderr)
                break
        
        return result
    
    def expand_word(self, word: str) -> str:
        """Expand variables, braces, and other patterns in a word"""
        # Check for brace expansion first
        if '{' in word and not (word.startswith("'") and word.endswith("'")):
            # Perform brace expansion
            brace_expansions = expand_braces(word)
            if len(brace_expansions) > 1:
                # Join the brace expansions with spaces
                expanded_word = ' '.join(brace_expansions)
                if self.debug_mode:
                    print(f"[DEBUG] Brace expansion: '{word}' -> '{expanded_word}'", file=sys.stderr)
                return expanded_word
        
        # Use the full expander for complete expansion
        expanded = expand_all(word)
        
        # Handle any environment variable expansion the expander missed
        # (especially for variables defined within the shell but not in environment)
        var_pattern = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_]*|\d+|[\*\@\#\?\$\!])')
        
        def replace_var(match):
            var_name = match.group(1)
            var_value = self.current_scope.get(var_name)
            if self.debug_mode:
                print(f"[DEBUG] Expanding ${var_name} to '{var_value}'", file=sys.stderr)
            return var_value or ''
            
        expanded = var_pattern.sub(replace_var, expanded)
        
        # Return expanded word
        return expanded
    
    def pattern_match(self, word: str, pattern: str) -> bool:
        """Match a word against a shell pattern"""
        # Handle special case of *) pattern
        if pattern == '*':
            return True
            
        return fnmatch.fnmatch(word, pattern)
    
    def handle_test_command(self, args: List[str]) -> int:
        """Handle the test command or [ command"""
        # Strip leading [ and trailing ] if present
        if args[0] == '[':
            if args[-1] != ']':
                raise ExecutionError("Missing closing bracket in test command")
            args = args[1:-1]
        else:
            # Remove 'test' from the beginning
            args = args[1:]
        
        if not args:
            return 1  # Empty test is false
        
        # Define operation handlers using dictionaries
        # File test operations (take one argument after the operator)
        file_tests = {
            '-e': os.path.exists,      # File exists
            '-f': os.path.isfile,      # Is a regular file
            '-d': os.path.isdir,       # Is a directory
        }
        
        # String comparison operations (take two arguments around the operator)
        string_tests = {
            '=': lambda a, b: a == b,   # String equality
            '!=': lambda a, b: a != b,  # String inequality
        }
        
        # Numeric comparison operations (take two arguments around the operator)
        def safe_numeric_compare(a: str, b: str, op: Callable[[int, int], bool]) -> bool:
            """Safely compare two strings as integers, returning False on ValueError"""
            try:
                return op(int(a), int(b))
            except ValueError:
                return False
                
        numeric_tests = {
            '-eq': lambda a, b: safe_numeric_compare(a, b, lambda x, y: x == y),  # Equal
            '-ne': lambda a, b: safe_numeric_compare(a, b, lambda x, y: x != y),  # Not equal
            '-lt': lambda a, b: safe_numeric_compare(a, b, lambda x, y: x < y),   # Less than
            '-le': lambda a, b: safe_numeric_compare(a, b, lambda x, y: x <= y),  # Less than or equal
            '-gt': lambda a, b: safe_numeric_compare(a, b, lambda x, y: x > y),   # Greater than
            '-ge': lambda a, b: safe_numeric_compare(a, b, lambda x, y: x >= y),  # Greater than or equal
        }
        
        # Handle file tests (format: -e file)
        if len(args) == 2 and args[0] in file_tests:
            return 0 if file_tests[args[0]](args[1]) else 1
            
        # Handle two-operand tests (format: arg1 OP arg2)
        if len(args) == 3:
            # String comparison
            if args[1] in string_tests:
                return 0 if string_tests[args[1]](args[0], args[2]) else 1
                
            # Numeric comparison
            if args[1] in numeric_tests:
                return 0 if numeric_tests[args[1]](args[0], args[2]) else 1
        
        # Default to false for unrecognized tests
        return 1