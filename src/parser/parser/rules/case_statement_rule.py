#!/usr/bin/env python3
"""
Rule for parsing case statements.
"""

from typing import List, Optional, Set, Tuple

from ...ast import Node, CaseNode, CaseItem, ListNode
from ...token_types import TokenType
from ..grammar_rule import GrammarRule
from ..token_stream import TokenStream
from ..parser_context import ParserContext
from .command_rule import CommandRule


class CaseStatementRule(GrammarRule):
    """
    Rule for parsing case statements like "case word in pattern) cmd;; esac".
    
    A case statement consists of a word to match, a series of patterns and actions,
    and is terminated by 'esac'.
    """
    
    def can_start_with(self) -> Set[TokenType]:
        """
        Get the set of token types that this rule can start with.
        
        Returns:
            A set containing TokenType.KEYWORD, since case statements start with 'case'
        """
        return {TokenType.KEYWORD}
    
    def can_start_with_keyword(self, keyword: str) -> bool:
        """
        Check if this rule can start with the given keyword.
        
        Args:
            keyword: The keyword to check
            
        Returns:
            True if keyword is 'case', False otherwise
        """
        return keyword == 'case'
    
    def parse(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a case statement from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A CaseNode representing the case statement, or None if parsing failed
        """
        # Check and consume the 'case' keyword
        if not stream.match_keyword('case'):
            return None
            
        # Get the word to match
        if stream.is_at_end() or stream.peek().token_type != TokenType.WORD:
            context.report_error(
                "Expected word after 'case'",
                stream.current_position(),
                "Add a word to match after 'case'"
            )
            return None
            
        word = stream.consume().value
        
        # Check and consume the 'in' keyword
        if not stream.match_keyword('in'):
            context.report_error(
                "Expected 'in' after case word",
                stream.current_position(),
                "Add 'in' after the case word"
            )
            context.mark_in_progress()
            return None
            
        # Parse the patterns and actions
        items = []
        
        while not stream.is_at_end():
            # Check if we've reached the end of the case statement
            if stream.match_keyword('esac'):
                break
                
            # Parse a pattern and its action
            item = self._parse_case_item(stream, context)
            if item is None:
                # If we can't parse a pattern, try to recover
                if stream.match_keyword('esac'):
                    break
                else:
                    # Skip to next pattern or esac
                    self._skip_to_next_pattern(stream)
                    continue
                    
            items.append(item)
            
        # Check if we've consumed 'esac' or reached the end of the stream
        if stream.is_at_end():
            context.report_error(
                "Expected 'esac' to close case statement",
                stream.current_position(),
                "Add 'esac' to close the case statement"
            )
            context.mark_in_progress()
            return None
            
        # Create and return case node
        return CaseNode(word, items)
    
    def _parse_case_item(self, stream: TokenStream, context: ParserContext) -> Optional[CaseItem]:
        """
        Parse a case item (pattern and action) from the token stream.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A CaseItem if successful, None otherwise
        """
        # Get the pattern
        if stream.is_at_end() or stream.peek().token_type != TokenType.WORD:
            return None
            
        pattern = stream.consume().value
        
        # Check for closing parenthesis
        if pattern.endswith(')'):
            # Pattern includes the closing parenthesis, strip it
            pattern = pattern[:-1]
        else:
            # Expect a closing parenthesis
            if not stream.match_operator(')'):
                context.report_error(
                    "Expected ')' after pattern",
                    stream.current_position(),
                    "Add ')' after the pattern"
                )
                return None
                
        # Parse the action (commands until ';;', ';&', or ';;& or 'esac')
        action = self._parse_command_list(stream, context)
        if action is None:
            context.report_error(
                "Expected commands for pattern",
                stream.current_position(),
                "Add commands for the pattern"
            )
            return None
            
        # Skip the pattern terminator
        if stream.match_operator(';'):
            # Check for ;; (another semicolon)
            if stream.match_operator(';'):
                # Found ;;
                pass
            elif stream.match_operator('&'):
                # Found ;& (fallthrough)
                pass
            # else just a single ; which is also valid
        
        # Create and return case item
        return CaseItem(pattern, action)
    
    def _parse_command_list(self, stream: TokenStream, context: ParserContext) -> Optional[Node]:
        """
        Parse a list of commands until a pattern terminator or 'esac' is encountered.
        
        Args:
            stream: The token stream to parse from
            context: The parser context for state and error reporting
            
        Returns:
            A Node representing the command list, or None if parsing failed
        """
        # Save the current position
        start_pos = stream.save_position()
        
        # Parse commands until a pattern terminator or 'esac' is encountered
        commands = []
        command_rule = CommandRule()
        
        # Add safety counter to prevent infinite loops
        max_iterations = len(stream.tokens) * 2  # Generous limit
        iteration_count = 0
        
        while not stream.is_at_end() and iteration_count < max_iterations:
            iteration_count += 1
            
            # Check if we've reached the end of the action
            token = stream.peek()
            if token is None:
                # Safety check - peek can sometimes return None
                break
                
            if token.token_type == TokenType.KEYWORD and token.value == 'esac':
                break
                
            if token.token_type == TokenType.OPERATOR and token.value == ';':
                break
                
            # Parse the next command
            command = command_rule.parse(stream, context)
            if command is not None:
                commands.append(command)
            else:
                # If we can't parse a command, skip to the next statement
                token = stream.consume()
                # If we encounter a terminator or 'esac', break
                if token is not None and ((token.token_type == TokenType.OPERATOR and token.value == ';') or \
                   (token.token_type == TokenType.KEYWORD and token.value == 'esac')):
                    # Unconsume the token so it can be processed by the caller
                    stream.restore_position(stream.current_position().index - 1)
                    break
        
        # If we hit the iteration limit, log a warning
        if iteration_count >= max_iterations:
            import sys
            print("[WARNING] Case command list parsing exceeded iteration limit - breaking infinite loop", file=sys.stderr)
                    
        # If no commands were parsed, return None
        if not commands:
            # Restore the stream position
            stream.restore_position(start_pos)
            return None
            
        # If there's only one command, return it directly
        if len(commands) == 1:
            return commands[0]
            
        # Otherwise, create a list node
        return ListNode(commands)
    
    def _skip_to_next_pattern(self, stream: TokenStream) -> None:
        """
        Skip tokens until the next pattern or the end of the case statement.
        
        Args:
            stream: The token stream to skip in
        """
        # Skip until we find ';;', ';&', ';;& or 'esac'
        # Add safety counter to prevent infinite loops
        max_iterations = len(stream.tokens) * 2  # Generous limit
        iteration_count = 0
        
        while not stream.is_at_end() and iteration_count < max_iterations:
            iteration_count += 1
            
            token = stream.peek()
            if token is None:
                # Safety check - peek can sometimes return None
                break
                
            # Check for pattern terminators
            if token.token_type == TokenType.OPERATOR and token.value == ';':
                stream.consume()  # Consume the first semicolon
                
                # Check for another semicolon
                if not stream.is_at_end() and stream.peek() is not None and stream.peek().token_type == TokenType.OPERATOR:
                    if stream.peek().value in {';', '&'}:
                        stream.consume()  # Consume the second separator
                        return
                else:
                    # Single semicolon is also a valid terminator
                    return
                    
            # Check for 'esac'
            if token.token_type == TokenType.KEYWORD and token.value == 'esac':
                return
                
            # Skip this token
            stream.consume()
            
        # If we hit the iteration limit, log a warning
        if iteration_count >= max_iterations:
            import sys
            print("[WARNING] Skip to next pattern exceeded iteration limit - breaking infinite loop", file=sys.stderr)