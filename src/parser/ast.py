#!/usr/bin/env python3

from typing import List, Dict, Optional, Any, Callable, Union
from abc import ABC, abstractmethod
from .lexer import Token

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


class Node(ABC):
    """Base class for all AST nodes"""
    
    @abstractmethod
    def accept(self, visitor: ASTVisitor) -> Any:
        """Accept a visitor to traverse this node"""
        pass


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
    
    def __repr__(self) -> str:
        return f"CommandNode(command={self.command!r}, args={self.args!r}, background={self.background})"


class PipelineNode(Node):
    """Represents a pipeline of commands"""
    
    def __init__(self, commands: List[CommandNode], background: bool = False):
        self.commands = commands
        self.background = background
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_pipeline(self)
    
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
    
    def __repr__(self) -> str:
        return f"ForNode(variable={self.variable!r}, words={self.words!r}, body={self.body!r})"


class CaseItem:
    """Represents a pattern-action pair in a case statement"""
    
    def __init__(self, pattern: str, action: Node):
        self.pattern = pattern
        self.action = action
    
    def __repr__(self) -> str:
        return f"CaseItem(pattern={self.pattern!r}, action={self.action!r})"


class CaseNode(Node):
    """Represents a case statement"""
    
    def __init__(self, word: str, items: List[CaseItem]):
        self.word = word
        self.items = items
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_case(self)
    
    def __repr__(self) -> str:
        return f"CaseNode(word={self.word!r}, items={self.items!r})"


class FunctionNode(Node):
    """Represents a function definition"""
    
    def __init__(self, name: str, body: Node):
        self.name = name
        self.body = body
    
    def accept(self, visitor: ASTVisitor) -> Any:
        return visitor.visit_function(self)
    
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
    
    def __repr__(self) -> str:
        return f"ListNode(nodes={self.nodes!r})"