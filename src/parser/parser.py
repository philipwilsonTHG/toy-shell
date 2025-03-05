#!/usr/bin/env python3

import sys
from typing import List, Optional, Tuple, Dict, Any
from .new.token_types import Token, TokenType
from .new.lexer import tokenize
from .new.redirection import RedirectionParser

# For compatibility with existing code
parse_redirections = RedirectionParser.parse_redirections
from .ast import (
    Node, CommandNode, PipelineNode, IfNode, WhileNode, 
    ForNode, CaseNode, FunctionNode, ListNode, CaseItem
)

class ParseError(Exception):
    """Exception raised for parser errors"""
    pass


class Parser:
    """Shell script parser that builds an AST"""
    
    def __init__(self):
        self.tokens: List[Token] = []
        self.current: int = 0
        self.in_progress: bool = False
        self.buffer: List[str] = []
    
    def parse(self, line: str) -> Optional[Node]:
        """Parse a single line or multi-line input into an AST"""
        # Add to buffer for multi-line statements
        self.buffer.append(line)
        
        try:
            # Try to parse the current buffer
            input_text = " ".join(self.buffer)
            
            # Check for incomplete statements
            if input_text.strip().endswith("if") or \
               input_text.strip().endswith("then") or \
               input_text.strip().endswith("else") or \
               input_text.strip().endswith("elif") or \
               input_text.strip().endswith("while") or \
               input_text.strip().endswith("until") or \
               input_text.strip().endswith("do") or \
               input_text.strip().endswith("for") or \
               input_text.strip().endswith("case") or \
               input_text.strip().endswith("in"):
                # These are clearly incomplete
                self.in_progress = True
                return None
                
            # Basic check if we start with a control statement but don't have the closing keyword
            if input_text.strip().startswith("if") and "fi" not in input_text:
                self.in_progress = True
                return None
                
            if input_text.strip().startswith("while") and "done" not in input_text:
                self.in_progress = True
                return None
                
            if input_text.strip().startswith("until") and "done" not in input_text:
                self.in_progress = True
                return None
                
            if input_text.strip().startswith("for") and "done" not in input_text:
                self.in_progress = True
                return None
                
            if input_text.strip().startswith("case") and "esac" not in input_text:
                self.in_progress = True
                return None
            
            self.tokens = tokenize(input_text)
            self.current = 0
            
            # Parse the program
            node = self.parse_program()
            
            # If we successfully parsed, reset the buffer
            self.buffer = []
            self.in_progress = False
            
            return node
        except ParseError as e:
            # Print the error for debugging
            print(f"Parse error: {e}")
            
            # If we have a parse error, it might be because we need more input
            # for a multi-line statement
            self.in_progress = True
            return None
    
    def is_incomplete(self) -> bool:
        """Check if the current parse attempt is incomplete"""
        return self.in_progress
    
    def reset(self):
        """Reset the parser state"""
        self.buffer = []
        self.in_progress = False
    
    def parse_program(self) -> Node:
        """Parse a complete program"""
        statements = []
        
        while not self.is_at_end():
            try:
                if self.check('keyword', 'if'):
                    self.advance()  # Consume 'if'
                    statements.append(self.parse_if_statement())
                elif self.check('keyword', 'while'):
                    self.advance()  # Consume 'while'
                    statements.append(self.parse_while_statement(False))
                elif self.check('keyword', 'until'):
                    self.advance()  # Consume 'until'
                    statements.append(self.parse_while_statement(True))
                elif self.check('keyword', 'for'):
                    self.advance()  # Consume 'for'
                    statements.append(self.parse_for_statement())
                elif self.check('keyword', 'case'):
                    self.advance()  # Consume 'case'
                    statements.append(self.parse_case_statement())
                elif self.check('keyword', 'function'):
                    self.advance()  # Consume 'function'
                    statements.append(self.parse_function_definition())
                else:
                    statements.append(self.parse_command())
                
                # Skip optional terminators and separators
                self.skip_separators()
            except Exception as e:
                print(f"Parse error: {e}")
                # Reset state to be incomplete
                self.in_progress = True
                return None
        
        if len(statements) == 1:
            return statements[0]
        
        return ListNode(statements)
    
    def parse_command(self) -> Node:
        """Parse a simple command or pipeline"""
        # Check for background execution
        has_background = False
        
        # Get tokens for command and check for pipe
        segments = []
        cmd_tokens = []
        
        while not self.is_at_end():
            token = self.peek()
            
            # End of command
            if token.token_type == TokenType.OPERATOR and token.value in {';', '&'}:
                self.advance()  # Consume the token
                if token.value == '&':
                    has_background = True
                
                if cmd_tokens:
                    segments.append(cmd_tokens)
                break
                
            # Pipeline character
            if token.token_type == TokenType.OPERATOR and token.value == '|':
                self.advance()  # Consume the token
                if cmd_tokens:
                    segments.append(cmd_tokens)
                    cmd_tokens = []
                else:
                    raise ParseError("Empty command before pipe")
                continue
            
            # Keywords that indicate end of command
            if token.token_type == TokenType.KEYWORD and token.value in {'then', 'else', 'elif', 'fi', 'do', 'done', 'esac'}:
                if cmd_tokens:
                    segments.append(cmd_tokens)
                break
            
            # Add current token to the command
            cmd_tokens.append(self.advance())
            
            # Handle end of input - moved here to handle termination properly
            if self.is_at_end():
                if cmd_tokens:
                    segments.append(cmd_tokens)
                break
        
        if not segments:
            return CommandNode("", [])
        
        # Build command nodes for each pipeline segment
        command_nodes = []
        
        for segment in segments:
            if not segment:
                continue
                
            # Extract redirections
            cmd_tokens, redirections = parse_redirections(segment)
            
            # Special check for 2>&1 redirection
            for i, (redir_op, redir_target) in enumerate(redirections):
                if redir_op == '2>' and redir_target == '&1':
                    # Convert to a special format for this specific pattern
                    redirections[i] = ('2>&1', '')
            
            if not cmd_tokens:
                raise ParseError("Empty command in pipeline")
            
            # Extract command name and arguments
            cmd_name = cmd_tokens[0].value
            
            # Process arguments for quoting
            from .quotes import is_quoted, strip_quotes
            args = []
            for token in cmd_tokens:
                token_value = token.value
                # If token is quoted, strip quotes before adding to args
                args.append(token_value)
            
            # Create command node
            command_nodes.append(CommandNode(cmd_name, args, redirections))
        
        if not command_nodes:
            return CommandNode("", [])
            
        if len(command_nodes) == 1:
            # Only create a single command node for simple commands
            cmd_node = command_nodes[0]
            cmd_node.background = has_background
            return cmd_node
        
        # Create a pipeline for multiple commands
        pipeline = PipelineNode(command_nodes, has_background)
        return pipeline
    
    def parse_if_statement(self) -> IfNode:
        """Parse an if statement"""
        # if was already consumed
        
        # Parse condition (commands until then)
        condition_statements = []
        while not self.is_at_end() and not self.check('keyword', 'then'):
            condition_statements.append(self.parse_command())
            self.skip_separators()
            
        if self.is_at_end():
            raise ParseError("Incomplete if statement, missing 'then'")
            
        # Consume 'then'
        self.advance()
        
        if len(condition_statements) == 0:
            raise ParseError("Empty condition in if statement")
        elif len(condition_statements) == 1:
            condition = condition_statements[0]
        else:
            condition = ListNode(condition_statements)
        
        # Parse then branch (commands until else, elif or fi)
        then_statements = []
        while not self.is_at_end() and not (self.check('keyword', 'else') or 
                                           self.check('keyword', 'elif') or 
                                           self.check('keyword', 'fi')):
            then_statements.append(self.parse_command())
            self.skip_separators()
            
        if self.is_at_end():
            raise ParseError("Incomplete if statement, missing 'fi'")
            
        if len(then_statements) == 0:
            then_branch = CommandNode("", [])  # Empty command as placeholder
        elif len(then_statements) == 1:
            then_branch = then_statements[0]
        else:
            then_branch = ListNode(then_statements)
        
        # Check for else or elif
        else_branch = None
        if self.check('keyword', 'else'):
            self.advance()  # Consume 'else'
            
            # Parse else branch (commands until fi)
            else_statements = []
            while not self.is_at_end() and not self.check('keyword', 'fi'):
                else_statements.append(self.parse_command())
                self.skip_separators()
                
            if len(else_statements) == 0:
                else_branch = CommandNode("", [])  # Empty command as placeholder
            elif len(else_statements) == 1:
                else_branch = else_statements[0]
            else:
                else_branch = ListNode(else_statements)
                
        elif self.check('keyword', 'elif'):
            self.advance()  # Consume 'elif'
            # Handle elif as a nested if statement
            else_branch = self.parse_if_statement()
        
        # Expect fi
        if not self.check('keyword', 'fi'):
            raise ParseError("Expected 'fi' to close if statement")
            
        self.advance()  # Consume 'fi'
        
        return IfNode(condition, then_branch, else_branch)
    
    def parse_while_statement(self, is_until: bool) -> WhileNode:
        """Parse a while or until loop"""
        # while/until was already consumed
        
        # Parse condition (commands until do)
        condition_statements = []
        while not self.is_at_end() and not self.check('keyword', 'do'):
            condition_statements.append(self.parse_command())
            self.skip_separators()
            
        if self.is_at_end():
            raise ParseError("Incomplete while/until statement, missing 'do'")
            
        # Consume 'do'
        self.advance()
        
        if len(condition_statements) == 0:
            raise ParseError("Empty condition in while/until statement")
        elif len(condition_statements) == 1:
            condition = condition_statements[0]
        else:
            condition = ListNode(condition_statements)
        
        # Parse body (commands until done)
        body_statements = []
        while not self.is_at_end() and not self.check('keyword', 'done'):
            body_statements.append(self.parse_command())
            self.skip_separators()
            
        if self.is_at_end():
            raise ParseError("Incomplete while/until statement, missing 'done'")
            
        # Consume 'done'
        self.advance()
        
        if len(body_statements) == 0:
            body = CommandNode("", [])  # Empty command as placeholder
        elif len(body_statements) == 1:
            body = body_statements[0]
        else:
            body = ListNode(body_statements)
        
        return WhileNode(condition, body, is_until)
    
    def parse_for_statement(self) -> ForNode:
        """Parse a for loop"""
        # for was already consumed
        
        # Get variable name
        if self.is_at_end() or self.peek().token_type != TokenType.WORD:
            raise ParseError("Expected variable name after 'for'")
        
        variable = self.advance().value
        
        # Expect in
        if not self.check('keyword', 'in'):
            raise ParseError("Expected 'in' after variable in for loop")
            
        self.advance()  # Consume 'in'
        
        # Parse words to iterate over
        words = []
        while not self.is_at_end() and not self.check('keyword', 'do'):
            token = self.advance()
            # Skip separators like semicolons
            if token.token_type == TokenType.OPERATOR and token.value == ';':
                continue
            words.append(token.value)
        
        if self.is_at_end():
            raise ParseError("Incomplete for statement, missing 'do'")
            
        # Consume 'do'
        self.advance()
        
        # Parse body (commands until done)
        body_statements = []
        while not self.is_at_end() and not self.check('keyword', 'done'):
            body_statements.append(self.parse_command())
            self.skip_separators()
            
        if self.is_at_end():
            raise ParseError("Incomplete for statement, missing 'done'")
            
        # Consume 'done'
        self.advance()
        
        if len(body_statements) == 0:
            body = CommandNode("", [])  # Empty command as placeholder
        elif len(body_statements) == 1:
            body = body_statements[0]
        else:
            body = ListNode(body_statements)
        
        return ForNode(variable, words, body)
    
    def parse_case_statement(self) -> CaseNode:
        """Parse a case statement"""
        # case was already consumed
        
        # Get word to match against - can be multiple tokens for $var
        if self.is_at_end():
            raise ParseError("Expected word after 'case'")
        
        # Handle special case for $var where '$' and 'var' are separate tokens
        if self.peek().value == '$' and not self.is_at_end(1) and self.tokens[self.current + 1].type == 'word':
            self.advance()  # consume $
            word = '$' + self.advance().value
        else:
            # Normal word
            word = self.advance().value
        
        # Expect in
        if not self.check('keyword', 'in'):
            raise ParseError("Expected 'in' after word in case statement")
            
        self.advance()  # Consume 'in'
        
        # Parse case items (pattern) action pairs
        items = []
        
        while not self.is_at_end() and not self.check('keyword', 'esac'):
            if self.is_at_end():
                raise ParseError("Incomplete case statement, missing pattern")
                
            # Get pattern - handle the case where pattern and ) are combined (e.g. "a)")
            pattern_token = self.advance().value
            
            # Check if the pattern ends with )
            if pattern_token.endswith(')'):
                pattern = pattern_token[:-1]  # Remove the trailing )
            else:
                # Separate pattern and )
                pattern = pattern_token
                
                # Expect )
                if self.is_at_end() or not (self.peek().token_type == TokenType.OPERATOR and self.peek().value == ')'):
                    raise ParseError("Expected ')' after pattern in case statement")
                
                self.advance()  # Consume ')'
            
            # Parse action (commands until ;; or esac)
            action_statements = []
            while not self.is_at_end() and not self.check('keyword', 'esac') and not (
                   self.peek().token_type == TokenType.OPERATOR and self.peek().value == ';'):
                action_statements.append(self.parse_command())
                self.skip_separators()
            
            # Process action node
            if len(action_statements) == 0:
                action = CommandNode("", [])  # Empty command as placeholder
            elif len(action_statements) == 1:
                action = action_statements[0]
            else:
                action = ListNode(action_statements)
            
            items.append(CaseItem(pattern, action))
            
            # Expect ;; or ;;& or ;& or end of case
            if self.is_at_end() or self.check('keyword', 'esac'):
                break
                
            # Skip ;; pattern separator
            if self.peek().token_type == TokenType.OPERATOR and self.peek().value == ';':
                self.advance()  # First ;
                if not self.is_at_end() and self.peek().token_type == TokenType.OPERATOR and self.peek().value == ';':
                    self.advance()  # Second ;
        
        if self.is_at_end():
            raise ParseError("Incomplete case statement, missing 'esac'")
            
        # Consume 'esac'
        self.advance()
        
        return CaseNode(word, items)
    
    def parse_function_definition(self) -> FunctionNode:
        """Parse a function definition"""
        # function was already consumed
        
        # Get function name
        if self.is_at_end() or self.peek().token_type != TokenType.WORD:
            raise ParseError("Expected function name")
        
        name = self.advance().value
        
        # Check for optional ()
        if not self.is_at_end() and self.peek().token_type == TokenType.OPERATOR and self.peek().value == '(':
            self.advance()  # Consume (
            
            if self.is_at_end() or self.peek().token_type != TokenType.OPERATOR or self.peek().value != ')':
                raise ParseError("Expected ')' after '(' in function definition")
            
            self.advance()  # Consume )
        
        # Get the function body - can be a compound statement or a single command
        # First check for compound statement wrapped in { }
        if not self.is_at_end() and self.peek().token_type == TokenType.OPERATOR and self.peek().value == '{':
            self.advance()  # Consume {
            
            # Parse body statements until }
            body_statements = []
            while not self.is_at_end() and not (self.peek().token_type == TokenType.OPERATOR and self.peek().value == '}'):
                body_statements.append(self.parse_command())
                self.skip_separators()
                
            if self.is_at_end():
                raise ParseError("Incomplete function definition, missing '}'")
                
            self.advance()  # Consume }
            
            if len(body_statements) == 0:
                body = CommandNode("", [])  # Empty command as placeholder
            elif len(body_statements) == 1:
                body = body_statements[0]
            else:
                body = ListNode(body_statements)
        else:
            # Parse a single command
            body = self.parse_command()
        
        return FunctionNode(name, body)
    
    def skip_separators(self):
        """Skip command separators (;)"""
        while not self.is_at_end() and self.peek().token_type == TokenType.OPERATOR and self.peek().value == ';':
            self.advance()
    
    def match(self, token_type_str: str, value: str = None) -> bool:
        """Check if current token matches and advance if it does"""
        if self.is_at_end():
            return False
        
        # Convert string type to TokenType enum
        token_type = TokenType.WORD
        if token_type_str == 'operator':
            token_type = TokenType.OPERATOR
        elif token_type_str == 'keyword':
            token_type = TokenType.KEYWORD
        elif token_type_str == 'substitution':
            token_type = TokenType.SUBSTITUTION
            
        if self.peek().token_type != token_type:
            return False
            
        if value is not None and self.peek().value != value:
            return False
            
        self.advance()
        return True
    
    def check(self, token_type_str: str, value: str = None) -> bool:
        """Check if current token matches without advancing"""
        if self.is_at_end():
            return False
        
        # Convert string type to TokenType enum
        token_type = TokenType.WORD
        if token_type_str == 'operator':
            token_type = TokenType.OPERATOR
        elif token_type_str == 'keyword':
            token_type = TokenType.KEYWORD
        elif token_type_str == 'substitution':
            token_type = TokenType.SUBSTITUTION
            
        if self.peek().token_type != token_type:
            return False
            
        if value is not None and self.peek().value != value:
            return False
            
        return True
    
    def advance(self) -> Token:
        """Advance to next token and return current token"""
        if not self.is_at_end():
            self.current += 1
        return self.tokens[self.current - 1]
    
    def peek(self) -> Token:
        """Return current token without advancing"""
        return self.tokens[self.current]
    
    def is_at_end(self, offset: int = 0) -> bool:
        """Check if we've reached the end of the tokens"""
        return self.current + offset >= len(self.tokens)
        
    def parse_dollar_var(self) -> str:
        """Parse a variable that might start with $ as a special case"""
        if self.peek().value == '$' and not self.is_at_end(1) and self.tokens[self.current + 1].type == 'word':
            self.advance()  # Consume $
            return '$' + self.advance().value
        else:
            return self.advance().value