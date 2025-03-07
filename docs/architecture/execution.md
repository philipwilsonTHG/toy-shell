# Python Shell Execution Architecture

The execution subsystem in the Python Shell (psh) project is responsible for executing parsed AST nodes, handling command execution, managing pipelines, and controlling process lifecycle. This document describes the execution architecture after refactoring.

## Directory Structure

```
src/execution/
├── __init__.py
├── ast_executor.py        # Executes AST nodes using visitor pattern
├── pipeline.py            # Handles pipeline execution and process creation
└── job_manager.py         # Manages background jobs and process control
```

## Core Components

### 1. AST Executor (`ast_executor.py`)

The AST Executor translates abstract syntax tree nodes into executable actions:

- Implements the visitor pattern with methods for each AST node type
- Maintains variable scoping through a scope chain
- Manages function definitions and calls
- Handles control flow (if/then/else, loops, case statements)
- Performs variable expansion and pattern matching
- Delegates actual command execution to the Pipeline Executor

Key classes:
- `ASTExecutor`: Main executor implementing the visitor pattern
- `FunctionRegistry`: Stores and manages shell function definitions
- `Scope`: Manages variable scopes with parent-child relationships

### 2. Pipeline Executor (`pipeline.py`)

The Pipeline Executor manages the actual execution of commands and pipelines:

- Creates and manages pipes between processes
- Handles file descriptor setup for redirections
- Manages process forking and execution
- Expands tokens (variables, wildcards) before execution
- Delegates to built-ins or executes external commands
- Preserves quoted arguments during expansion

Key classes:
- `PipelineExecutor`: Orchestrates command execution
- `TokenExpander`: Expands variables and performs globbing
- `RedirectionHandler`: Manages file descriptor setup for redirections

### 3. Job Manager (`job_manager.py`)

The Job Manager provides job control capabilities:

- Tracks background and suspended processes
- Manages process groups for terminal control
- Handles job state transitions (running, stopped, completed)
- Implements foreground/background switching (fg/bg)
- Supports job status reporting

Key class:
- `JobManager`: Central job control management

## Execution Flow

### 1. Command/Pipeline Execution

1. **AST Traversal**: AST Executor visits nodes in the syntax tree
2. **Command Preparation**:
   - Variables are expanded
   - Quotes are processed
   - Redirections are prepared
3. **Pipeline Setup**:
   - For pipelines, pipes are created between commands
   - Processes are forked for each command
4. **Process Setup**:
   - File descriptors are set up for redirections and pipes
   - Process groups are established for job control
5. **Command Execution**:
   - Built-ins are executed directly in the shell process
   - External commands use `execvp` syscall
6. **Job Tracking**:
   - Background commands are registered as jobs
   - Foreground commands wait for completion
   - Exit status is collected and returned

### 2. Control Structure Execution

For control structures (if, while, for, case):

1. **Condition Evaluation**:
   - For if/while, conditions are executed as commands
   - Exit status determines control flow
2. **Branch Selection**:
   - Based on conditions, appropriate branch is selected
   - For loops iterate over expanded word lists
   - Case statements pattern-match against expressions
3. **Scope Management**:
   - Local variables are properly scoped
   - Function calls create new variable scopes
4. **Command Execution**:
   - Commands within structures are executed recursively

## Redirection and Pipe Handling

The redirection system supports:

- Input redirection (`<`)
- Output redirection (`>`, `>>`)
- Error redirection (`2>`, `2>>`)
- File descriptor duplication (`2>&1`)
- Pipeline connections between commands

Redirections are applied using low-level file descriptor operations:
1. Save original file descriptors if needed
2. Open target files with appropriate flags
3. Duplicate file descriptors using `dup2`
4. Close temporary file descriptors

## Job Control

Job control enables:

- Background execution with `&`
- Process suspension with Ctrl-Z
- Foreground/background switching with `fg`/`bg`
- Job status reporting with `jobs`

Implementation details:
1. Process groups track related processes
2. Terminal foreground process group controls signal handling
3. SIGCHLD handlers track process status changes
4. Job table maintains process state information

## Interaction with Builtins

Built-in commands:
- Execute in the main shell process (no fork)
- Can modify shell state (environment, directory, etc.)
- Return exit codes like external commands
- Are checked first before external command lookup

## Error Handling

The execution system provides:
- Descriptive error messages for execution failures
- Proper exit status propagation
- Signal handling for interrupts and termination
- Resource cleanup for aborted commands

## Benefits of the Architecture

1. **Clean Separation**: AST execution separate from process management
2. **Flexible Control Flow**: Support for all shell control structures
3. **Proper Variable Scoping**: Local and global variable management
4. **Efficient Process Handling**: Minimal process creation
5. **Robust Job Control**: Full featured background job management

This architecture provides a solid foundation for shell execution, balancing complexity with capabilities typical of a modern shell.