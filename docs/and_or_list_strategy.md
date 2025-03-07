# Strategy for Implementing AND-OR Lists in psh

## Overview

AND-OR lists in POSIX shells allow conditional execution based on the success or failure of previous commands:

- `cmd1 && cmd2` - Execute cmd2 only if cmd1 succeeds (exit status 0)
- `cmd1 || cmd2` - Execute cmd2 only if cmd1 fails (non-zero exit status)
- Complex chains: `cmd1 && cmd2 || cmd3 && cmd4` - Evaluated left to right with proper short-circuit logic

## Implementation Strategy

### 1. Parser Enhancement

First, modify the parser to recognize `&&` and `||` operators:

```python
class ShellParser:
    def __init__(self):
        # Existing initialization...
        self.and_or_operators = ['&&', '||']
    
    def parse_command_line(self, tokens):
        # Split tokens on && and || operators
        segments = []
        current_segment = []
        
        for token in tokens:
            if token.value in self.and_or_operators:
                if current_segment:
                    segments.append((current_segment, None))
                    current_segment = []
                segments[-1] = (segments[-1][0], token.value)
            else:
                current_segment.append(token)
        
        if current_segment:
            segments.append((current_segment, None))
            
        return self.parse_and_or_list(segments)
```

### 2. AST Representation

Create a dedicated node type for AND-OR lists:

```python
class AndOrNode(Node):
    """
    Represents an AND-OR list of commands connected by && or || operators.
    """
    def __init__(self, commands_with_operators):
        """
        Initialize with list of (command_node, operator) tuples where:
        - command_node is any executable node (Command, Pipeline, etc.)
        - operator is either '&&', '||', or None (for the last command)
        """
        self.commands_with_operators = commands_with_operators
    
    def __repr__(self):
        return f"AndOrNode({self.commands_with_operators})"
        
    def accept(self, visitor):
        return visitor.visit_and_or(self)
```

### 3. AST Executor Implementation

Add a visitor method to execute AND-OR lists with proper short-circuit evaluation:

```python
def visit_and_or(self, node: AndOrNode) -> int:
    """Execute an AND-OR list with short-circuit evaluation."""
    last_result = 0
    
    for command, operator in node.commands_with_operators:
        # Execute the current command
        last_result = self.execute(command)
        
        # Handle short-circuit behavior
        if operator == '&&' and last_result != 0:
            # AND operation with failure - short-circuit and skip the rest
            break
        elif operator == '||' and last_result == 0:
            # OR operation with success - short-circuit and skip the rest
            break
    
    return last_result
```

### 4. Token Stream Management

Enhance the TokenStream class to handle AND-OR operators:

```python
class TokenStream:
    def split_on_and_or(self):
        """Split the stream on && and || operators."""
        segments = []
        current_tokens = []
        operator = None
        
        while not self.is_at_end():
            token = self.peek()
            
            if token.value in ['&&', '||']:
                segments.append((current_tokens, operator))
                operator = token.value
                current_tokens = []
                self.advance()  # Consume the operator
            else:
                current_tokens.append(token)
                self.advance()
        
        # Add the final segment
        if current_tokens:
            segments.append((current_tokens, None))
            
        return segments
```

### 5. Integration with Execution Pipeline

Modify the main execution flow to use the AND-OR list handling:

```python
def execute_line(self, line):
    tokens = tokenize(line)
    
    # First check for AND-OR lists
    if any(token.value in ['&&', '||'] for token in tokens):
        and_or_node = self.parser.parse_and_or_list(tokens)
        return self.executor.execute(and_or_node)
    
    # Existing execution logic for simple commands and pipelines...
```

### 6. Error Handling

Add proper error handling for malformed AND-OR lists:

```python
def parse_and_or_list(self, tokens):
    # Check for errors like missing commands between operators
    for i, token in enumerate(tokens):
        if token.value in ['&&', '||']:
            if i == 0 or i == len(tokens) - 1:
                raise SyntaxError(f"Syntax error near unexpected token '{token.value}'")
            if tokens[i-1].value in ['&&', '||'] or tokens[i+1].value in ['&&', '||']:
                raise SyntaxError(f"Syntax error near unexpected token '{token.value}'")
```

### 7. Handling Precedence with Other Operators

Ensure correct interaction with other shell operators:

```python
def parse_command_line(self, tokens):
    # Handle semicolons first (command lists)
    commands = self.split_on_semicolons(tokens)
    
    # Then handle AND-OR lists for each command
    result_nodes = []
    for command_tokens in commands:
        if any(t.value in ['&&', '||'] for t in command_tokens):
            result_nodes.append(self.parse_and_or_list(command_tokens))
        else:
            # Parse as regular command/pipeline
            result_nodes.append(self.parse_pipeline(command_tokens))
    
    return CommandListNode(result_nodes)
```

### 8. Testing Strategy

Create comprehensive tests for AND-OR lists:

1. Basic functionality:
   - `cmd1 && cmd2` (cmd2 runs if cmd1 succeeds)
   - `cmd1 || cmd2` (cmd2 runs if cmd1 fails)

2. Short-circuit behavior:
   - `true && echo yes` (outputs "yes")
   - `false && echo no` (outputs nothing)
   - `false || echo yes` (outputs "yes")
   - `true || echo no` (outputs nothing)

3. Complex chains:
   - `true && echo a && echo b` (outputs "a" and "b")
   - `false && echo a || echo b` (outputs "b" only)
   - `true || echo a && echo b` (outputs "b" only)

4. Error handling:
   - `&& echo error` (syntax error)
   - `echo test &&` (syntax error)
   - `echo a && && echo b` (syntax error)

## Operator Precedence Rules

POSIX specifies the following precedence for shell operators, from highest to lowest:

1. Command and field splitting (spaces)
2. Redirection operators (`>`, `<`, `2>`, etc.)
3. Pipe operator (`|`)
4. AND-OR operators (`&&`, `||`) - left-to-right
5. Command separator (`;`, `&`)

The implementation must respect this precedence order to ensure that complex command lines are parsed correctly.