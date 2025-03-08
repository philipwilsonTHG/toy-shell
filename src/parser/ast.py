#!/usr/bin/env python3

import sys
from typing import List, Dict, Optional, Any, Callable, Union, TextIO
from abc import ABC, abstractmethod
from .token_types import Token

class ASTVisitor(ABC):
    """Base visitor class for AST traversal"""
    
    @abstractmethod
    def visit_command(self, node: 'CommandNode') -> Any:
        pass
    
    @abstractmethod
    def visit_pipeline(self, node: 'PipelineNode') -> Any:
        pass
    
    @abstractmethod
    def visit_if(self, node: 'IfNode') -> Any:
        pass
    
    @abstractmethod
    def visit_while(self, node: 'WhileNode') -> Any:
        pass
    
    @abstractmethod
    def visit_for(self, node: 'ForNode') -> Any:
        pass
    
    @abstractmethod
    def visit_case(self, node: 'CaseNode') -> Any:
        pass
    
    @abstractmethod
    def visit_function(self, node: 'FunctionNode') -> Any:
        pass
        
    @abstractmethod
    def visit_and_or(self, node: 'AndOrNode') -> Any:
        pass


class Node(ABC):
    """Base class for all AST nodes"""
    
    @abstractmethod
    def accept(self, visitor: ASTVisitor) -> Any:
        """Accept a visitor to traverse this node"""
        pass
        
    @abstractmethod
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        pass

def print_ast_debug(node: Optional[Node], indent: int = 0, file: TextIO = sys.stderr) -> None:
    """Helper function to print an AST node with proper handling for None"""
    if node is None:
        prefix = "  " * indent
        print(f"{prefix}None", file=file)
    else:
        node.print_debug(indent, file)


class CommandNode(Node):
    """Represents a simple command with arguments and redirections"""
    
    def __init__(self, command: str, args: List[str], redirections: List[tuple] = None, 
                 background: bool = False):
        self.command = command
        self.args = args
        self.redirections = redirections or []
        self.background = background
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_command(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
    
    def __repr__(self) -> str:
        return f"CommandNode(command={self.command!r}, args={self.args!r}, background={self.background})"


class PipelineNode(Node):
    """Represents a pipeline of commands"""
    
    def __init__(self, commands: List[CommandNode], background: bool = False):
        self.commands = commands
        self.background = background
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_pipeline(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        for i, cmd in enumerate(self.commands):
            print(f"{prefix}  Command {i+1}:", file=file)
            print_ast_debug(cmd, indent + 2, file)
    
    def __repr__(self) -> str:
        return f"PipelineNode(commands={self.commands!r}, background={self.background})"


class IfNode(Node):
    """Represents an if-then-else construct"""
    
    def __init__(self, condition: Node, then_branch: Node, else_branch: Optional[Node] = None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_if(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        print(f"{prefix}  Condition:", file=file)
        print_ast_debug(self.condition, indent + 2, file)
        print(f"{prefix}  Then branch:", file=file)
        print_ast_debug(self.then_branch, indent + 2, file)
        if self.else_branch:
            print(f"{prefix}  Else branch:", file=file)
            print_ast_debug(self.else_branch, indent + 2, file)
    
    def __repr__(self) -> str:
        return f"IfNode(condition={self.condition!r}, then={self.then_branch!r}, else={self.else_branch!r})"


class WhileNode(Node):
    """Represents a while loop construct"""
    
    def __init__(self, condition: Node, body: Node, until: bool = False):
        self.condition = condition
        self.body = body
        self.until = until  # True for until loops, False for while loops
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_while(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        print(f"{prefix}  Condition:", file=file)
        print_ast_debug(self.condition, indent + 2, file)
        print(f"{prefix}  Body:", file=file)
        print_ast_debug(self.body, indent + 2, file)
    
    def __repr__(self) -> str:
        loop_type = "until" if self.until else "while"
        return f"{loop_type.capitalize()}Node(condition={self.condition!r}, body={self.body!r})"


class ForNode(Node):
    """Represents a for loop construct"""
    
    def __init__(self, variable: str, words: List[str], body: Node):
        self.variable = variable
        self.words = words
        self.body = body
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_for(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        print(f"{prefix}  Variable: {self.variable}", file=file)
        print(f"{prefix}  Words: {self.words}", file=file)
        print(f"{prefix}  Body:", file=file)
        print_ast_debug(self.body, indent + 2, file)
    
    def __repr__(self) -> str:
        return f"ForNode(variable={self.variable!r}, words={self.words!r}, body={self.body!r})"


class CaseItem:
    """Represents a pattern-action pair in a case statement"""
    
    def __init__(self, pattern: str, action: Node):
        self.pattern = pattern
        self.action = action
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the item with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        print_ast_debug(self.action, indent + 1, file)
    
    def __repr__(self) -> str:
        return f"CaseItem(pattern={self.pattern!r}, action={self.action!r})"


class CaseNode(Node):
    """Represents a case statement"""
    
    def __init__(self, word: str, items: List[CaseItem]):
        self.word = word
        self.items = items
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_case(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        print(f"{prefix}  Word: {self.word}", file=file)
        for i, item in enumerate(self.items):
            print(f"{prefix}  Pattern {i+1} ({item.pattern}):", file=file)
            print_ast_debug(item.action, indent + 2, file)
    
    def __repr__(self) -> str:
        return f"CaseNode(word={self.word!r}, items={self.items!r})"


class FunctionNode(Node):
    """Represents a function definition"""
    
    def __init__(self, name: str, body: Node):
        self.name = name
        self.body = body
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_function(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        print(f"{prefix}  Body:", file=file)
        print_ast_debug(self.body, indent + 2, file)
    
    def __repr__(self) -> str:
        return f"FunctionNode(name={self.name!r}, body={self.body!r})"


class ListNode(Node):
    """Represents a list of nodes (compound statement)"""
    
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
    
    def accept(self, visitor: ASTVisitor) -> Any:
        results = []
        for node in self.nodes:
            results.append(node.accept(visitor))
        return results
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        for i, node in enumerate(self.nodes):
            print(f"{prefix}  Node {i+1}:", file=file)
            print_ast_debug(node, indent + 2, file)
    
    def __repr__(self) -> str:
        return f"ListNode(nodes={self.nodes!r})"


class AndOrNode(Node):
    """
    Represents an AND-OR list of commands connected by && or || operators.
    
    In POSIX shells, AND-OR lists allow conditional execution based on success or failure:
    - cmd1 && cmd2 - Execute cmd2 only if cmd1 succeeds (exit status 0)
    - cmd1 || cmd2 - Execute cmd2 only if cmd1 fails (non-zero exit status)
    """
    
    def __init__(self, commands_with_operators: List[tuple]):
        """
        Initialize with list of (command_node, operator) tuples where:
        - command_node is any executable node (Command, Pipeline, etc.)
        - operator is either '&&', '||', or None (for the last command)
        """
        self.commands_with_operators = commands_with_operators
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_and_or(self)
    
    def print_debug(self, indent: int = 0, file: TextIO = sys.stderr) -> None:
        """Print a debug representation of the node with proper indentation"""
        prefix = "  " * indent
        print(f"{prefix}{self!r}", file=file)
        for i, (cmd, op) in enumerate(self.commands_with_operators):
            op_str = f" {op} " if op else " (end)"
            print(f"{prefix}  Command {i+1}{op_str}:", file=file)
            print_ast_debug(cmd, indent + 2, file)
    
    def __repr__(self) -> str:
        return f"AndOrNode(commands_with_operators={self.commands_with_operators!r})"