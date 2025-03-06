# Migration Guide: Transitioning to the New Parser API

This document provides guidance for transitioning from the old parser API to the new parser API.

## Background

The shell's parser implementation has been completely refactored for better maintainability, extensibility, and error handling. The new implementation:

- Uses a modular design with grammar-specific rule classes
- Provides better error reporting and recovery
- Supports more complex shell constructs
- Has improved performance and stability

This refactoring includes both the lexer and parser components. Key benefits of the new API include:

- Better type safety with enums like `TokenType`
- More object-oriented design with proper methods and classes
- Consistent API for all parsing operations
- Improved error handling and reporting
- Support for more complex shell scripting features

## Core Changes

### Parser Class

**Old API:**
```python
from src.parser import Parser

# Create parser
parser = Parser()

# Parse a line
node = parser.parse("echo hello world")

# Check for incomplete input
if parser.is_incomplete():
    # Need more input
    more_input = input("> ")
    node = parser.parse(more_input)
```

**New API:**
```python
from src.parser import ShellParser

# Create parser
parser = ShellParser()

# Parse a single line
node = parser.parse_line("echo hello world")

# For multi-line input
node1 = parser.parse_multi_line("if test -f /etc/passwd")
# node1 is None, need more input
node2 = parser.parse_multi_line("then echo exists; fi")
# node2 is the complete AST
```

### Token Class

**Old API:**
```python
# This is already covered in the legacy migration guide
from src.parser import Token
token = Token("value", "word")
```

**New API:**
```python
from src.parser import Token, TokenType

# Use enum for types
token = Token("value", TokenType.WORD)

# Type comparison uses enum
if token.token_type == TokenType.OPERATOR:
    # handle operator

# Or use helper methods
if token.is_operator():
    # handle operator
```

### Low-level Parsing Components

**Old API:**
```python
from src.parser import tokenize, parse_redirections, split_pipeline

tokens = tokenize("command arg1 arg2 > output.txt")
cmd_tokens, redirections = parse_redirections(tokens)
segments = split_pipeline(tokens)
```

**New API:**
```python
from src.parser import tokenize, parse_redirections, split_pipeline

# The low-level functions have the same names and signatures
tokens = tokenize("command arg1 arg2 > output.txt")
cmd_tokens, redirections = parse_redirections(tokens)
segments = split_pipeline(tokens)
```

## Migration Steps

### 1. Update Imports

Replace imports from the old API with imports from the new modules:

```python
# Before
from src.parser import Parser

# After
from src.parser import ShellParser
```

For more direct access to components, you can use these imports:

```python
# For direct access to components
from src.parser import Token, TokenType, tokenize
from src.parser import parse_redirections, split_pipeline
```

### 2. Replace Parser Usage

Replace the old `Parser` class with the new `ShellParser`:

```python
# Before
parser = Parser()
node = parser.parse("echo hello world")

# After
parser = ShellParser()
node = parser.parse_line("echo hello world")
```

For multi-line parsing:

```python
# Before
parser = Parser()
result1 = parser.parse("if [ -f /etc/hosts ]")  # Returns None, incomplete
result2 = parser.parse("then echo exists; fi")  # Returns complete AST

# After
parser = ShellParser()
result1 = parser.parse_multi_line("if [ -f /etc/hosts ]")  # Returns None, incomplete
result2 = parser.parse_multi_line("then echo exists; fi")  # Returns complete AST
```

### 3. Use Token Type Enums

Replace string comparisons with enum comparisons:

```python
# Before
if token.type == "operator":
    # handle operator

# After
if token.token_type == TokenType.OPERATOR:
    # handle operator
# Or better:
if token.is_operator():
    # handle operator
```

## New Features

The new parser API provides several advanced features:

1. **Direct Access to Parser Rules** 
   
   For complex parsing tasks, you can access the rule classes directly:

   ```python
   from src.parser.new.parser.rules import CommandRule, PipelineRule, IfStatementRule
   from src.parser.new.parser.token_stream import TokenStream
   from src.parser.new.parser.parser_context import ParserContext
   
   # Set up the context
   stream = TokenStream(tokens)
   context = ParserContext()
   
   # Use a specific rule
   if_rule = IfStatementRule()
   if_node = if_rule.parse(stream, context)
   ```

2. **Token Type Checking Methods**
   ```python
   # Check if a token is an operator
   if token.is_operator():
       # ...
       
   # Check if a token is a specific operator
   if token.is_operator("|"):
       # ...
       
   # Check if a token is a keyword
   if token.is_keyword():
       # ...
   ```

3. **Factory Functions for Tokens**
   ```python
   from src.parser.new.token_types import create_word_token, create_operator_token
   
   # Create a word token
   word = create_word_token("value", quoted=True)
   
   # Create an operator token
   op = create_operator_token("|")
   ```

4. **Parser Context for Error Handling**
   ```python
   from src.parser.new.parser.parser_context import ParserContext
   
   context = ParserContext()
   # After parsing, check for errors
   if context.has_error():
       print(f"Error: {context.get_error_message()}")
   ```

## Migration Status

1. **Previous State**: Old parser implementation with compatibility layer
2. **Current State**: New parser implementation, old parser removed
   - All code must use the new ShellParser or its components
   - Core codebase has been fully migrated to the new parser API

## Example: Complete Migration

Here's a complete example of migrating a shell script parsing function:

```python
# Before
from src.parser import Parser

def parse_script(script_content):
    parser = Parser()
    lines = script_content.split('\n')
    ast_nodes = []
    
    for line in lines:
        node = parser.parse(line)
        if node is not None:
            ast_nodes.append(node)
    
    return ast_nodes

# After
from src.parser import ShellParser

def parse_script(script_content):
    parser = ShellParser()
    # The new parser can handle the entire script at once
    node = parser.parse_line(script_content)
    return [node] if node else []
```

## Testing Your Migration

After migrating to the new API, run the full test suite to ensure everything works correctly:

```bash
pytest
```

The test suite includes extensive tests for the new parser implementation.