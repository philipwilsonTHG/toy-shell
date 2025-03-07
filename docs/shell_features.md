# Python Shell (psh) Features

This document describes the features supported by the Python Shell (psh), including both basic shell functionality and advanced features.

## Basic Shell Features

### Command Execution
- Run external commands and built-in commands
- Proper exit status handling with `$?` variable
- Command sequences with semicolons: `cmd1; cmd2; cmd3`

### Redirections
```bash
command > file       # Redirect stdout to file
command >> file      # Append stdout to file
command < file       # Redirect stdin from file
command 2> file      # Redirect stderr to file
command 2>> file     # Append stderr to file
command &> file      # Redirect both stdout and stderr to file
command 2>&1         # Redirect stderr to stdout
```

### Pipelines
```bash
command1 | command2 | command3  # Pipe output between commands
command1 |& command2           # Pipe both stdout and stderr
```

### Variables
```bash
VAR=value            # Set variable
echo $VAR            # Use variable
export VAR=value     # Export variable to environment
unset VAR            # Remove variable
```

### Quoting
```bash
echo "Double quotes $VAR"     # Variables expanded
echo 'Single quotes $VAR'     # Variables not expanded
echo \$VAR                    # Escaped variables not expanded
```

## Advanced Features

### Arithmetic Expansion

The shell supports arithmetic expansion using the POSIX `$(( expression ))` syntax:

```bash
# Basic arithmetic
echo $((1 + 2))         # Outputs: 3
echo $((10 * 5))        # Outputs: 50
echo $((20 / 4))        # Outputs: 5

# Variables in arithmetic expressions
x=10
y=5
echo $((x + y))         # Outputs: 15
echo $((x * y))         # Outputs: 50

# Complex expressions
echo $((1 + 2 * 3))     # Outputs: 7 (follows operator precedence)
echo $(((1 + 2) * 3))   # Outputs: 9 (parentheses change precedence)

# Logical operators
echo $((1 && 1))        # Outputs: 1 (true)
echo $((1 || 0))        # Outputs: 1 (true)
echo $((0 || 0))        # Outputs: 0 (false)
echo $((!0))            # Outputs: 1 (true)

# Ternary operator
echo $((x > y ? x : y)) # Outputs: 10 (x is greater)

# Nested arithmetic expressions
echo $((1 + $((2 * 3)))) # Outputs: 7
```

### Command Substitution

```bash
files=$(ls)            # Store command output in variable
echo "Date: $(date)"   # Embed command output in string
wc -l $(find . -name "*.py")  # Use command output as arguments
```

### Control Structures

#### If Statements
```bash
if [ -f file.txt ]; then
    echo "File exists"
elif [ -d directory ]; then
    echo "Directory exists"
else
    echo "Neither exists"
fi
```

#### For Loops
```bash
for i in 1 2 3 4 5; do
    echo "Item: $i"
done

for file in *.txt; do
    echo "Processing $file"
done
```

#### While Loops
```bash
i=1
while [ $i -le 5 ]; do
    echo "Count: $i"
    i=$((i + 1))
done
```

#### Case Statements
```bash
case "$1" in
    start)
        echo "Starting service"
        ;;
    stop)
        echo "Stopping service"
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        ;;
esac
```

### Job Control

```bash
command &             # Run in background
jobs                  # List background jobs
fg %N                 # Bring job N to foreground
bg %N                 # Resume job N in background
Ctrl+Z                # Suspend foreground job
```

### History

```bash
history               # Show command history
history N             # Show last N commands
history -c            # Clear history
!!                    # Repeat last command
!N                    # Repeat command number N
!string               # Repeat last command starting with string
Ctrl+R                # Search history
```

## Implementation Details

The Python Shell features are implemented through:

1. **Lexer & Parser**: Tokenizes input and builds an AST (Abstract Syntax Tree)
2. **Expander**: Handles variable, command, and arithmetic expansion
3. **Executor**: Executes AST nodes and manages processes
4. **Job Manager**: Handles background jobs and process groups
5. **Builtins**: Implements shell built-in commands

All features aim to be POSIX-compliant while providing a clean Python-based implementation.