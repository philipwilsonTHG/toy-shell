# Python Shell Parser Architecture

The refactored parser in the Python Shell (psh) project follows a modular, rule-based architecture that provides a clean separation of concerns and improved maintainability. This document outlines the current parser architecture after the recent refactoring.

## Directory Structure

```
src/parser/
├── __init__.py             # Public API exports
├── ast.py                  # AST node definitions
├── expander.py             # Variable and command expansion
├── lexer.py                # Tokenization
├── parser/                 # Core parser implementation
│   ├── grammar_rule.py     # Base class for grammar rules
│   ├── parser_context.py   # Parser state and error handling
│   ├── rules/              # Grammar rule implementations
│   │   ├── command_rule.py
│   │   ├── pipeline_rule.py
│   │   ├── if_statement_rule.py
│   │   ├── for_statement_rule.py
│   │   └── ...
│   ├── shell_parser.py     # Main parser orchestration
│   └── token_stream.py     # Token stream management
├── quotes.py               # Quote handling utilities
└── token_types.py          # Token definitions
```

## Core Components

### 1. Lexer/Tokenization (`lexer.py`, `token_types.py`)
- Transforms input text into a stream of typed tokens
- Identifies token types: WORD, OPERATOR, KEYWORD, etc.
- Handles quoting, escaping, and special characters
- Preserves quote information for expansion control

### 2. Token Stream (`token_stream.py`)
- Provides cursor-like interface for token consumption
- Supports lookahead with `peek()` and `peek_type()`
- Enables backtracking and position tracking
- Offers utility methods for common patterns (`match()`, `expect()`)

### 3. Grammar Rules (`rules/*.py`)
- Each shell construct has its own dedicated rule class
- Rules implement the `GrammarRule` abstract base class
- Each rule knows how to parse its specific construct
- Rules include predictive methods to guide rule selection

### 4. Shell Parser (`shell_parser.py`)
- Central coordinator for the parsing process
- Selects appropriate rules based on current token
- Handles error recovery and synchronization
- Maintains parser context and state

### 5. AST Nodes (`ast.py`)
- Hierarchical node structure representing shell programs
- Implements visitor pattern for traversal
- Node types include:
  - `CommandNode`: Simple commands
  - `PipelineNode`: Piped commands
  - `IfNode`, `WhileNode`, `ForNode`: Control structures
  - `FunctionNode`: Function definitions
  - `ListNode`: Command sequences

## Parsing Process

1. **Tokenization**: Input is broken into tokens by the lexer
2. **Rule Selection**: ShellParser examines the current token
3. **Rule Application**: Selected rule consumes tokens and builds AST
4. **Recursive Parsing**: Rules may invoke other rules for nested structures
5. **AST Construction**: Complete AST is built representing the program

## Control Structures

Each control structure is handled by a dedicated rule:

- **If Statements**: `if condition; then commands; [elif...;] [else...;] fi`
- **While Loops**: `while condition; do commands; done`
- **For Loops**: `for var in words; do commands; done`
- **Case Statements**: `case word in pattern) commands;; ... esac`
- **Functions**: `function name() { commands; }`

## Error Handling

- Detailed error messages with position information
- Synchronization points for error recovery
- Support for multi-line input with continuation
- Context-aware error suggestions

## Benefits of the New Architecture

1. **Modularity**: Each grammar construct has a focused implementation
2. **Maintainability**: Smaller, focused classes with clear responsibilities
3. **Extensibility**: Easy to add new syntax by adding grammar rules
4. **Testability**: Rules can be tested in isolation
5. **Improved Error Handling**: Better error messages and recovery

This architecture represents a significant improvement over the previous monolithic parser implementation, providing a solid foundation for future enhancements to the shell.