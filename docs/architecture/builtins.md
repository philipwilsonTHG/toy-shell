# Python Shell Builtins Architecture

The builtins subsystem in the Python Shell (psh) project implements shell commands that are executed directly by the shell process rather than as separate programs. This document outlines the architecture of the builtins implementation.

## Directory Structure

```
src/builtins/
├── __init__.py           # Exports the BUILTINS dictionary
├── core.py               # Core shell commands (cd, exit, etc.)
├── env.py                # Environment variable management
├── eval.py               # Expression evaluation
├── history.py            # Command history management
└── jobs.py               # Job control commands
```

## Core Components

### 1. Builtins Registry (`__init__.py`)

The builtins registry is a central dictionary mapping command names to their implementations:

```python
BUILTINS: Dict[str, Callable[..., Any]] = {
    "cd": cd,
    "exit": exit_shell,
    "version": version,
    "export": export,
    "unset": unset,
    "jobs": jobs,
    "bg": bg,
    "fg": fg,
    "history": history,
    "eval": eval_expr,
    ".": source,
    "source": source
}
```

This registry enables:
- Command name lookup during execution
- Alternative command names for the same function (e.g., `.` and `source`)
- Easy addition of new builtins

### 2. Builtin Categories

Builtins are organized into logical categories, each in a separate module:

#### Core Commands (`core.py`)
- `cd`: Change current working directory
- `exit_shell`: Exit the shell with optional status code
- `version`: Display shell version information
- `source`: Execute commands from a file

#### Environment Management (`env.py`)
- `export`: Set or display environment variables
- `unset`: Remove environment variables

#### Job Control (`jobs.py`)
- `jobs`: List active jobs
- `bg`: Resume job in background
- `fg`: Bring job to foreground

#### History Management (`history.py`)
- `history`: Display or manipulate command history

#### Expression Evaluation (`eval.py`)
- `eval_expr`: Evaluate and execute shell expressions

### 3. Integration with Shell

Builtins are integrated with the shell execution pipeline:

1. In `execution/pipeline.py`, the `PipelineExecutor` checks if a command exists in the `BUILTINS` dictionary
2. If found, it executes the builtin directly instead of forking a new process
3. Builtins have access to the global `SHELL` context for state management
4. Exit status from builtins is captured and used like external commands

## Builtin Implementation Pattern

Each builtin follows a consistent implementation pattern:

1. **Function Signature**:
   - Strongly typed parameters and return values
   - Optional parameters with appropriate defaults
   - Clear docstrings describing usage

2. **Error Handling**:
   - Descriptive error messages to stderr
   - Consistent return values (0 for success, non-zero for failure)
   - Exception handling with specific error messages

3. **Shell Integration**:
   - Access to the global `SHELL` context as needed
   - Modification of shell state through appropriate interfaces
   - Proper cleanup of resources

## Special Implementation Details

### Exit Command

The `exit_shell` builtin uses a special return value mechanism:

```python
def exit_shell(status_code: str = "0") -> int:
    code = int(status_code) if status_code.isnumeric() else 0
    code = code & 0xFF  # Ensure code is in 0-255 range
    return -1000 - code  # Special marker for shell to exit
```

The shell interprets values <= -1000 as signals to exit with status code `abs(value) - 1000`.

### Source Command

The `source` builtin creates a new shell instance to execute commands from a file:

```python
from ..shell import Shell
shell = Shell(debug_mode=False)
script_content = f.read()
result = shell.execute_line(script_content)
```

This approach maintains consistent shell behavior between interactive and script mode.

### Job Control Commands

Job control builtins interact with the shell's job table:

```python
def jobs():
    job_manager = JobManager()
    job_list = job_manager.list_jobs()
    for job in job_list:
        print(job_manager.format_job_info(job))
```

They use a `JobManager` interface to maintain abstraction from the direct job table implementation.

## Execution Flow

When executing a builtin command:

1. The shell parser converts input into a command node or tokens
2. The `PipelineExecutor` identifies the command as a builtin
3. Arguments are expanded and processed
4. The builtin function is called with the expanded arguments
5. The function performs its operation, potentially modifying shell state
6. A return code is provided back to the caller
7. The shell continues execution based on the return code

## Error Handling

Builtins implement consistent error handling:

1. Input validation with specific error messages
2. Try/except blocks for operations that may fail
3. Error messages written to stderr
4. Return codes that reflect success (0) or specific failures (1-255)

## Benefits of the Architecture

1. **Modular Organization**: Related builtins grouped in separate files
2. **Consistent Interface**: All builtins follow the same parameter/return pattern
3. **Clear Integration**: Well-defined integration with the shell execution pipeline
4. **Extensibility**: Easy to add new builtins
5. **Type Safety**: Strong typing throughout the implementation

The builtins architecture provides a clean, well-organized approach to implementing shell commands that need direct access to the shell's internal state.