# Migration Guide: Transitioning to the New Lexer API

This document provides guidance for transitioning from the compatibility layer to the new lexer API.

## Background

The shell's lexer implementation has been refactored for better maintainability and extensibility. During this process, we created a compatibility layer to ensure existing code continued to work without modification. Now that the refactoring is complete, migrating to the new API directly will provide several benefits:

- Better type safety with the `TokenType` enum
- More object-oriented design with proper token methods
- Improved performance by eliminating translation overhead
- Access to additional token features not available in the legacy API

## Core Changes

### Token Class

**Old (Compatibility Layer):**
```python
from src.parser import Token

# Old constructor with string type
token = Token("value", "word")  

# Type is a string
if token.type == "operator":
    # handle operator

# Token attribute was a direct field
token.quoted = True  
```

**New API:**
```python
from src.parser.new.token_types import Token, TokenType, create_word_token

# Use enum for types
token = Token("value", TokenType.WORD)

# Type comparison uses enum
if token.token_type == TokenType.OPERATOR:
    # handle operator

# Or use helper methods
if token.is_operator():
    # handle operator
   
# For creating common tokens, use factory functions
token = create_word_token("value", quoted=True)
```

### Tokenization

**Old (Compatibility Layer):**
```python
from src.parser import tokenize, parse_redirections, split_pipeline

tokens = tokenize("command arg1 arg2 > output.txt")
cmd_tokens, redirections = parse_redirections(tokens)
segments = split_pipeline(tokens)
```

**New API:**
```python
from src.parser.new.lexer import tokenize
from src.parser.new.redirection import RedirectionParser

tokens = tokenize("command arg1 arg2 > output.txt")
cmd_tokens, redirections = RedirectionParser.parse_redirections(tokens)
segments = RedirectionParser.split_pipeline(tokens)
```

## Migration Steps

### 1. Update Imports

Replace imports from the compatibility layer with direct imports from the new modules:

```python
# Before
from src.parser import Token, tokenize, parse_redirections, split_pipeline

# After
from src.parser.new.token_types import Token, TokenType, create_word_token
from src.parser.new.lexer import tokenize
from src.parser.new.redirection import RedirectionParser
```

### 2. Update Token Creation

Replace string-based token types with enum values:

```python
# Before
token = Token("value", "word")

# After
token = Token("value", TokenType.WORD)
# Or use the helper functions
token = create_word_token("value")
```

### 3. Update Token Access

Update how you access token attributes:

```python
# Before
if token.type == "operator":
    # ...
    
# After
if token.token_type == TokenType.OPERATOR:
    # ...
    
# Or use the convenience methods
if token.is_operator():
    # ...
```

### 4. Update Redirection Handling

Use the `RedirectionParser` class directly:

```python
# Before
cmd_tokens, redirections = parse_redirections(tokens)
segments = split_pipeline(tokens)

# After
cmd_tokens, redirections = RedirectionParser.parse_redirections(tokens)
segments = RedirectionParser.split_pipeline(tokens)
```

## New Features

The new API provides several features that weren't available in the legacy API:

1. **Token Type Checking Methods**
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

2. **Factory Functions**
   ```python
   from src.parser.new.token_types import create_word_token, create_operator_token
   
   # Create a word token
   word = create_word_token("value", quoted=True)
   
   # Create an operator token
   op = create_operator_token("|")
   ```

3. **Redirection Utilities**
   ```python
   from src.parser.new.redirection import RedirectionType, RedirectionParser
   
   # Check redirection type
   if RedirectionParser.get_redirection_type(token) == RedirectionType.STDOUT:
       # ...
   ```

## Deprecation Timeline

1. **Current State**: Compatibility layer is in place, old lexer.py removed
2. **Phase 1** (Next Release): Mark compatibility layer as deprecated with warnings
3. **Phase 2** (Future Release): Remove compatibility layer completely

## Example: Complete Migration

Here's a complete example of migrating a function from the old API to the new API:

```python
# Before
from src.parser import Token, tokenize, parse_redirections

def process_command(command_line):
    tokens = tokenize(command_line)
    for token in tokens:
        if token.type == "operator" and token.value == "|":
            print("Found pipe operator")
    
    cmd_tokens, redirections = parse_redirections(tokens)
    return cmd_tokens

# After
from src.parser.new.token_types import TokenType
from src.parser.new.lexer import tokenize
from src.parser.new.redirection import RedirectionParser

def process_command(command_line):
    tokens = tokenize(command_line)
    for token in tokens:
        if token.is_operator("|"):
            print("Found pipe operator")
    
    cmd_tokens, redirections = RedirectionParser.parse_redirections(tokens)
    return cmd_tokens
```

## Testing Your Migration

After migrating to the new API, be sure to run all tests to ensure everything still works correctly:

```bash
pytest
```

If you encounter any issues during migration, please report them to the project maintainers.