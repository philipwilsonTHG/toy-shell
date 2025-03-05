# Parser Refactoring Plan

## 1. Current Issues

The current parser implementation has several limitations:

1. **Monolithic Structure**: A single large Parser class with many interrelated methods
2. **String-based Type Checking**: Still using string comparisons in check/match methods 
3. **Error Recovery**: Limited ability to recover from parsing errors
4. **State Management**: Complex state tracking with variables like in_progress
5. **Testing Difficulty**: Hard to test individual parsing components
6. **Code Duplication**: Similar patterns repeated across many parse_* methods

## 2. Proposed Architecture

### 2.1 Core Components

1. **TokenStream**: A dedicated class to manage token consumption and lookahead
   ```python
   class TokenStream:
       def peek(self, offset=0) -> Token: ...
       def consume(self) -> Token: ...
       def match(self, token_type: TokenType, value=None) -> bool: ...
       def position(self) -> Position: ...  # Line/column for error reporting
   ```

2. **Grammar Rules**: Isolated classes for different grammar constructs
   ```python
   class GrammarRule(ABC):
       @abstractmethod
       def parse(self, stream: TokenStream) -> Node: ...
   
   class CommandRule(GrammarRule):
       def parse(self, stream: TokenStream) -> CommandNode: ...
   
   class IfStatementRule(GrammarRule):
       def parse(self, stream: TokenStream) -> IfNode: ...
   ```

3. **ParserContext**: Shared context for symbol tables, error reporting
   ```python
   class ParserContext:
       def report_error(self, message: str, position: Position): ...
       def enter_scope(self): ...
       def exit_scope(self): ...
   ```

4. **Predictive Parser**: Root parser that selects the appropriate rule
   ```python
   class ShellParser:
       def __init__(self): 
           self.rules = {
               TokenType.KEYWORD: {
                   "if": IfStatementRule(),
                   "for": ForLoopRule(),
                   # ...
               },
               TokenType.WORD: CommandRule(),
               # ...
           }
       
       def parse(self, tokens: List[Token]) -> Node: ...
   ```

### 2.2 Error Handling

1. **Error Recovery**: Ability to skip to known sync points (like `;`, `done`, etc.)
2. **Rich Error Context**: Include line/column and suggestion for fixes
3. **Partial AST**: Return a partial AST even with errors, marking invalid sections

### 2.3 State Management

1. **Parser State**: Encapsulate parser state in a dedicated object
2. **State Stack**: Push/pop state for nested constructs
3. **Breadcrumbs**: Track parsing context for better error messages

## 3. Implementation Strategy

### Phase 1: Introduce Core Infrastructure

1. Create TokenStream class to replace direct token access
2. Implement Position tracking for better errors
3. Add basic ParserContext

### Phase 2: Extract Grammar Rules

1. Start with CommandRule (most fundamental)
2. Extract PipelineRule
3. Move to control structures (if, while, for)
4. Add case and function handlers

### Phase 3: Implement New ShellParser

1. Create ShellParser using extracted rules
2. Implement rule selection based on lookahead
3. Add proper error reporting and recovery

### Phase 4: Transition and Testing

1. Create compatibility layer for existing code
2. Gradually migrate tests to new parser
3. Replace the old parser in the shell code

## 4. Example Implementation

```python
# Example TokenStream implementation
class TokenStream:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        
    def peek(self, offset=0) -> Optional[Token]:
        if self.position + offset >= len(self.tokens):
            return None
        return self.tokens[self.position + offset]
        
    def consume(self) -> Token:
        token = self.peek()
        self.position += 1
        return token
        
    def match(self, token_type: TokenType, value=None) -> bool:
        token = self.peek()
        if not token or token.token_type != token_type:
            return False
        if value is not None and token.value != value:
            return False
        self.consume()
        return True

# Example Grammar Rule for 'if' statements
class IfStatementRule(GrammarRule):
    def parse(self, stream: TokenStream, context: ParserContext) -> IfNode:
        # 'if' keyword already consumed
        
        # Parse condition
        condition = self.parse_command_list(stream, context, end_tokens=["then"])
        
        # Expect 'then'
        if not stream.match(TokenType.KEYWORD, "then"):
            context.report_error("Expected 'then' after condition", stream.position())
            return None
            
        # Parse 'then' branch
        then_branch = self.parse_command_list(
            stream, context, end_tokens=["else", "elif", "fi"])
            
        # Handle else/elif/fi
        else_branch = None
        token = stream.peek()
        
        if token and token.token_type == TokenType.KEYWORD:
            if token.value == "else":
                stream.consume()
                else_branch = self.parse_command_list(
                    stream, context, end_tokens=["fi"])
            elif token.value == "elif":
                stream.consume()
                else_branch = IfStatementRule().parse(stream, context)
                
        # Expect 'fi'
        if not stream.match(TokenType.KEYWORD, "fi"):
            context.report_error("Expected 'fi' to close if statement", stream.position())
            return None
            
        return IfNode(condition, then_branch, else_branch)
        
    def parse_command_list(self, stream: TokenStream, context: ParserContext, 
                          end_tokens: List[str]) -> Node:
        """Parse a list of commands until one of the end tokens is found"""
        commands = []
        
        while (token := stream.peek()) and not (
                token.token_type == TokenType.KEYWORD and token.value in end_tokens):
            commands.append(CommandRule().parse(stream, context))
            
        if len(commands) == 1:
            return commands[0]
        return ListNode(commands)
```

## 5. Benefits

1. **Maintainability**: Smaller, focused classes with clear responsibilities
2. **Extensibility**: Easy to add new syntax features by adding grammar rules
3. **Testability**: Test individual grammar rules in isolation
4. **Error Handling**: Better error messages with recovery
5. **Code Quality**: Reduced duplication and clearer structure

## 6. Migration Path

Similar to the lexer migration, we can:

1. Implement the new parser alongside the existing one
2. Create a compatibility layer
3. Gradually transition code to use the new parser
4. Eventually remove the compatibility layer

This approach minimizes risk while still providing the benefits of the refactored design.