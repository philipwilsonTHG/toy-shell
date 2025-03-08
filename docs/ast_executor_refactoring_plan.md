# AST Executor Refactoring Plan

## 1. Current Structure and Responsibilities

The `ast_executor.py` file implements an AST (Abstract Syntax Tree) executor for a shell language. It uses the visitor pattern to traverse and execute different node types in the syntax tree. Key responsibilities include:

- Function registry management (lines 23-39)
- Variable scope management (lines 42-67)
- AST execution through visitor methods (lines 70-471)
- Word expansion, including variables, braces, and globs (lines 473-503)
- Pattern matching for case statements (lines 505-511)
- Test command handling (lines 513-582)

## 2. Specific Refactoring Targets

### 2.1 Code Duplication in Command and Pipeline Processing
**Lines 186-251 and 268-330**
Duplicate logic for handling token creation, expansion, and redirection between `visit_command` and `visit_pipeline`.

```python
# In visit_command (line 192-246)
fixed_command = self._handle_escaped_dollars(node.command)
expanded_command = self.expand_word(fixed_command)
...
# Almost identical logic in visit_pipeline (line 276-321)
fixed_command = self._handle_escaped_dollars(cmd.command)
expanded_command = self.expand_word(fixed_command)
```

### 2.2 Overly Complex Test Command Handling
**Lines 513-582**
The `handle_test_command` function uses repetitive if-statements for each test operation.

```python
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
# ...and so on for each comparison operator
```

### 2.3 Complex _print_ast Method
**Lines 101-140**
The `_print_ast` method contains nested if-statements for each node type.

```python
# Recursively print child nodes
if isinstance(node, ListNode):
    for child in node.nodes:
        self._print_ast(child, indent + 1)
elif isinstance(node, IfNode):
    print(f"{prefix}  Condition:", file=sys.stderr)
    self._print_ast(node.condition, indent + 2)
    # ...more code
```

### 2.4 Late Importing
**Lines 186 and 270**
Importing modules inside functions:

```python
# Line 186
from ..parser.token_types import Token, TokenType, create_word_token

# Line 270 (duplicate import)
from ..parser.token_types import Token, TokenType, create_word_token
```

### 2.5 Inconsistent Error Handling
**Line 18-20**
`ExecutionError` is defined but rarely used in the code.

### 2.6 Global State in Expansion
**Lines 473-503**
The word expansion logic accesses instance variables directly, making it harder to test in isolation.

## 3. Refactoring Recommendations

### 3.1 Extract Command Processing Logic
Create a helper method to process commands and arguments to tokens, used by both `visit_command` and `visit_pipeline`:

```python
def _process_command_to_tokens(self, command: str, args: List[str], 
                             redirections: List[Tuple[str, str]]) -> List[Token]:
    """Convert a command, its args, and redirections to tokens with expansion."""
    tokens = []
    # Command expansion logic
    # Argument processing logic
    # Redirection processing logic
    return tokens
```

### 3.2 Refactor Test Command Handler
Use a dictionary-based approach for test operations:

```python
def handle_test_command(self, args: List[str]) -> int:
    # Strip brackets handling logic...
    
    # Define operation handlers
    file_tests = {
        '-e': os.path.exists,
        '-f': os.path.isfile,
        '-d': os.path.isdir
    }
    
    string_tests = {
        '=': lambda a, b: a == b,
        '!=': lambda a, b: a != b
    }
    
    numeric_tests = {
        '-eq': lambda a, b: int(a) == int(b),
        '-ne': lambda a, b: int(a) != int(b),
        '-lt': lambda a, b: int(a) < int(b),
        # other operators...
    }
    
    # Handle tests based on argument length and operator
    if len(args) == 2 and args[0] in file_tests:
        return 0 if file_tests[args[0]](args[1]) else 1
    
    if len(args) == 3:
        if args[1] in string_tests:
            return 0 if string_tests[args[1]](args[0], args[2]) else 1
        
        if args[1] in numeric_tests:
            try:
                return 0 if numeric_tests[args[1]](args[0], args[2]) else 1
            except ValueError:
                return 1
    
    return 1  # Default to false
```

### 3.3 Move AST Printing to Node Classes
Refactor to use polymorphism - each node type should know how to print itself:

```python
# In the AST module, add a method to each node class:
def debug_print(self, indent: int = 0, file=sys.stderr):
    """Print node details for debugging"""
    prefix = "  " * indent
    print(f"{prefix}{self}", file=file)
    # Node-specific child printing
```

### 3.4 Fix Imports
Move all imports to the top of the file, following Python style guidelines:

```python
# At top of file
import os
import re
import sys
import fnmatch
import glob  # Currently imported inside visit_for
from typing import Dict, List, Optional, Any, Tuple, Callable

from ..parser.ast import (...)
from ..execution.pipeline import PipelineExecutor
from ..context import SHELL
from ..parser.expander import expand_all, expand_braces
from ..parser.token_types import Token, TokenType, create_word_token
```

### 3.5 Create Dedicated Expander Class
Extract the expansion logic to a separate class:

```python
class WordExpander:
    """Handles expansion of words including variables, braces, and globs"""
    
    def __init__(self, scope_provider, debug_mode=False):
        self.scope_provider = scope_provider
        self.debug_mode = debug_mode
    
    def expand(self, word: str) -> str:
        """Expand a word with all expansions"""
        # Brace expansion logic
        # Variable expansion logic
        return expanded
```

### 3.6 Implement Better Error Handling
Use the `ExecutionError` consistently throughout the codebase:

```python
def handle_test_command(self, args: List[str]) -> int:
    if args[0] == '[' and args[-1] != ']':
        raise ExecutionError("Missing closing bracket in test command")
    # Rest of the method...
```

## 4. Prioritized Refactoring Tasks

1. **Extract Command Processing Logic (High Impact)**
   - Reduces duplication between `visit_command` and `visit_pipeline`
   - Improves maintainability and consistency
   - Makes future modifications easier

2. **Move Imports to Top Level (Easy Win)**
   - Quick improvement for code organization
   - Follows Python best practices
   - Prevents potential import-related bugs

3. **Refactor Test Command Handler (High Impact)**
   - Simplifies complex conditional logic
   - Makes test command handling more maintainable
   - Easier to add new test operations

4. **Create Dedicated Expander Class (Medium Impact)**
   - Improves separation of concerns
   - Makes expansion logic more testable
   - Reduces complexity in the executor class

5. **Implement Better Error Handling (Medium Impact)**
   - Improves error reporting and debugging
   - Makes behavior more consistent
   - Enhances user experience

6. **Move AST Printing to Node Classes (Lower Priority)**
   - Follows OOP principles better
   - Simplifies the executor class
   - Makes debugging output more maintainable

The primary focus should be on reducing duplication and complexity, which will significantly improve the maintainability of this critical component of the shell implementation.