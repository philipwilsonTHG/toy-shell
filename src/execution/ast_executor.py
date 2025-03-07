#!/usr/bin/env python3

import os
import re
import sys
import fnmatch
from typing import Dict, List, Optional, Any, Tuple

from ..parser.ast import (
    ASTVisitor, Node, CommandNode, PipelineNode, IfNode, WhileNode,
    ForNode, CaseNode, FunctionNode, ListNode, CaseItem
)
from ..execution.pipeline import PipelineExecutor
from ..context import SHELL


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
            return self.handle_test_command(node.args)
        
        # Regular command execution using pipeline executor
        from ..parser.token_types import Token, TokenType, create_word_token
        
        # Create tokens from command, expanding variables
        tokens = []
        
        # Handle escaped dollar signs first (before expansion)
        fixed_command = self._handle_escaped_dollars(node.command)
        expanded_command = self.expand_word(fixed_command)
        tokens.append(create_word_token(expanded_command))
        
        for arg in node.args[1:]:
            # Check if we need to preserve spaces for quotes
            is_quoted_arg = (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'"))
            
            # First handle escaped dollar signs, converting \$ to $ prior to expansion
            fixed_arg = self._handle_escaped_dollars(arg)
            
            # Expand the argument
            expanded_arg = self.expand_word(fixed_arg)
            
            # For debugging
            if self.debug_mode:
                print(f"[DEBUG] Processing arg: '{arg}' => '{expanded_arg}' (quoted: {is_quoted_arg})", file=sys.stderr)
            
            # Create a special token attribute to mark quoted arguments
            token = create_word_token(expanded_arg, quoted=is_quoted_arg)
            tokens.append(token)
            
        # Add redirections with variable expansion
        for redir_op, redir_target in node.redirections:
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
            
        # Execute the command
        result = self.pipeline_executor.execute_pipeline(tokens, node.background)
        self.last_status = result if result is not None else 0
        return self.last_status
        
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
        from ..parser.token_types import Token, TokenType, create_word_token
        
        tokens = []
        for i, cmd in enumerate(node.commands):
            # Add command and args with variable expansion
            fixed_command = self._handle_escaped_dollars(cmd.command)
            expanded_command = self.expand_word(fixed_command)
            tokens.append(create_word_token(expanded_command))
            
            for arg in cmd.args[1:]:
                fixed_arg = self._handle_escaped_dollars(arg)
                expanded_arg = self.expand_word(fixed_arg)
                tokens.append(create_word_token(expanded_arg))
            
            # Add redirections with variable expansion
            for redir_op, redir_target in cmd.redirections:
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
                import glob
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
    
    def expand_word(self, word: str) -> str:
        """Expand variables in a word"""
        # Replace variables with their values
        expanded = word
        
        # Handle escaped dollar signs (convert \$ to $)
        escaped_pattern = re.compile(r'\\(\$)')
        expanded = escaped_pattern.sub(r'\1', expanded)
        
        # Special case for quoted strings - remove quotes and handle separately
        if (word.startswith('"') and word.endswith('"')):
            inner_content = word[1:-1]
            # Apply variable expansion on the inner content
            expanded = inner_content
            
            # Simple variable expansion
            var_pattern = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_]*|\d+|[\*\@\#\?\$\!])')
            
            def replace_var(match):
                var_name = match.group(1)
                var_value = self.current_scope.get(var_name)
                if self.debug_mode:
                    print(f"[DEBUG] Expanding ${var_name} to '{var_value}' in quoted string", file=sys.stderr)
                return var_value or ''
                
            expanded = var_pattern.sub(replace_var, expanded)
            return expanded
        
        # Simple variable expansion
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
                return 1  # Missing closing bracket
            args = args[1:-1]
        else:
            # Remove 'test' from the beginning
            args = args[1:]
        
        if not args:
            return 1  # Empty test is false
            
        # Handle simple file tests
        if len(args) == 2 and args[0] == '-e':
            return 0 if os.path.exists(args[1]) else 1
        
        if len(args) == 2 and args[0] == '-f':
            return 0 if os.path.isfile(args[1]) else 1
            
        if len(args) == 2 and args[0] == '-d':
            return 0 if os.path.isdir(args[1]) else 1
            
        # Handle string comparison
        if len(args) == 3 and args[1] == '=':
            return 0 if args[0] == args[2] else 1
            
        if len(args) == 3 and args[1] == '!=':
            return 0 if args[0] != args[2] else 1
            
        # Handle numeric comparison
        if len(args) == 3 and args[1] == '-eq':
            try:
                return 0 if int(args[0]) == int(args[2]) else 1
            except ValueError:
                return 1
                
        if len(args) == 3 and args[1] == '-ne':
            try:
                return 0 if int(args[0]) != int(args[2]) else 1
            except ValueError:
                return 1
                
        if len(args) == 3 and args[1] == '-lt':
            try:
                return 0 if int(args[0]) < int(args[2]) else 1
            except ValueError:
                return 1
                
        if len(args) == 3 and args[1] == '-le':
            try:
                return 0 if int(args[0]) <= int(args[2]) else 1
            except ValueError:
                return 1
                
        if len(args) == 3 and args[1] == '-gt':
            try:
                return 0 if int(args[0]) > int(args[2]) else 1
            except ValueError:
                return 1
                
        if len(args) == 3 and args[1] == '-ge':
            try:
                return 0 if int(args[0]) >= int(args[2]) else 1
            except ValueError:
                return 1
                
        # Default to false for unrecognized tests
        return 1