# Python Shell (psh) Architecture

This document outlines the architecture of the Python Shell (psh) project, a POSIX-compatible shell implemented in Python.

## Project Overview

The Python Shell is a functional implementation of a Unix shell that supports common shell features including:
- Command execution
- Pipelines and redirections
- Variable expansion
- Command substitution
- Job control
- Control structures (if/then/else, loops, case statements)
- Shell functions
- Quoted argument handling
- Wildcard expansion

## High-Level Architecture

The shell is organized into several key components:

1. **Main Shell Interface** (`src/shell.py`): The entry point and primary controller
2. **Parser Subsystem** (`src/parser/`): Tokenization, AST building, and expansion
3. **Execution Engine** (`src/execution/`): Command and pipeline execution
4. **Built-in Commands** (`src/builtins/`): Implementation of shell builtins
5. **Context and State Management** (`src/context.py`): Global shell state
6. **Utilities** (`src/utils/`): Helper functions for history, completion, etc.
7. **Configuration** (`src/config/`): Shell configuration

## Component Details

### 1. Main Shell Interface (`src/shell.py`)

The `Shell` class is the primary entry point that:
- Processes command-line arguments
- Maintains the interactive REPL (Read-Eval-Print Loop)
- Routes input to the parser and execution components
- Handles signals and terminal control
- Manages job control

### 2. Parser Subsystem (`src/parser/`)

#### Lexer (`src/parser/lexer.py`)
- Tokenizes input string into `Token` objects
- Handles quote recognition and processing
- Identifies operators, keywords, and word tokens
- Processes command line splitting and redirection syntax

#### AST Builder (`src/parser/parser.py`)
- Converts token stream into Abstract Syntax Tree (AST)
- Handles control structures and command grouping
- Builds nested command representations
- Manages multi-line input collection

#### AST Nodes (`src/parser/ast.py`)
- Defines node types for different shell constructs:
  - `CommandNode`: Simple commands
  - `PipelineNode`: Commands connected with pipes
  - `IfNode`, `WhileNode`, `ForNode`, `CaseNode`: Control structures
  - `FunctionNode`: Shell function definitions
  - `ListNode`: Sequence of commands

#### Expander (`src/parser/expander.py`)
- Handles various types of shell expansions:
  - Brace expansion (`{a,b,c}`, `{1..5}`)
  - Variable expansion (`$VAR`, `${VAR}`)
  - Command substitution (`$(cmd)`, <code>\`cmd\`</code>)
  - Tilde expansion (`~`)
  - Wildcard expansion (`*`, `?`, `[...]`)

#### Quote Handling (`src/parser/quotes.py`)
- Processes quoted strings
- Determines proper expansion behavior based on quote types
- Preserves spaces in quoted arguments

### 3. Execution Engine (`src/execution/`)

#### AST Executor (`src/execution/ast_executor.py`)
- Implements visitor pattern for executing AST nodes
- Maintains variable scopes
- Handles control flow (if/else, loops)
- Manages function registry and execution

#### Pipeline Executor (`src/execution/pipeline.py`)
- Handles execution of command pipelines
- Creates and manages pipes between processes
- Handles input/output redirection
- Expands tokens before execution
- Manages process forking and execution
- Preserves quoted arguments during execution

#### Job Manager (`src/execution/job_manager.py`)
- Tracks background jobs
- Manages job status and control
- Handles foreground/background job transitions

### 4. Built-in Commands (`src/builtins/`)

The shell implements various built-in commands:
- `core.py`: Core builtins (cd, exit, source)
- `env.py`: Environment variable management (export, unset)
- `jobs.py`: Job control (jobs, bg, fg)
- `history.py`: History management
- `eval.py`: Expression evaluation

### 5. Context Management (`src/context.py`)

The `SHELL` global context object tracks:
- Current working directory
- Environment variables
- Job information
- Shell status
- History state

### 6. Utilities (`src/utils/`)

- `completion.py`: Command-line completion
- `history.py`: Command history management
- `terminal.py`: Terminal control and signal handling

### 7. Configuration (`src/config/`)

- `manager.py`: Handles shell configuration settings

## Data Flow

1. Input is read from stdin or a script file
2. The shell tokenizes the input with the lexer
3. The parser converts tokens into an AST
4. The AST executor evaluates the AST nodes
5. For command execution, the pipeline executor:
   - Handles expansions (variables, wildcards, etc.)
   - Creates pipes and redirections
   - Forks processes for execution
   - Manages job control and waits for completion
6. Results are displayed to the user
7. The shell returns to the prompt for more input

## Key Components for Quote Handling

The quote handling system involves coordination between multiple components:

1. **Tokenization** (`lexer.py`):
   - Identifies and marks quoted strings
   - Preserves quotes during tokenization
   - Sets the `quoted` attribute on tokens

2. **Expansion** (`expander.py`):
   - Handles variable expansion within double quotes
   - Preserves literals in single quotes
   - Properly handles nested quotes

3. **Execution** (`pipeline.py`):
   - Preserves quoted arguments as single tokens
   - Prevents word splitting in quoted strings
   - Passes quoted arguments intact to child processes

## Testing Architecture

The testing infrastructure is organized by component:
- `tests/test_builtins/`: Tests for built-in commands
- `tests/test_parser/`: Tests for lexer, parser, and expander
- `tests/test_execution/`: Tests for command execution
- `tests/test_utils/`: Tests for utility functions

Each component has individual test cases that verify functionality and regression tests to prevent regressions.

## Future Development

The architecture is designed for extensibility in several areas:
- Support for more shell features (arrays, arithmetic expansion)
- Enhanced control structures
- More advanced pattern matching
- Improved completion and history support
- Enhanced scripting capabilities with additional AST node types