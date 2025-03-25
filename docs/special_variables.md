# Special Variables in POSIX Shells

## Overview

POSIX-compliant shells like psh support a standard set of special parameters (variables) that provide information about the shell environment, process status, and command line arguments. These variables are automatically set by the shell and can be accessed using the `$` prefix.

## Process Information

| Variable | Description | Example Usage |
|----------|-------------|---------------|
| `$$` | Current shell's process ID (PID) | `echo "Shell PID: $$"` |
| `$!` | PID of the most recently backgrounded process | `sleep 10 & echo "Background PID: $!"` |
| `$?` | Exit status of the most recently executed foreground command | `grep pattern file; echo "Exit status: $?"` |
| `$-` | Current shell option flags | `echo "Shell flags: $-"` |
| `$0` | Name of the shell or shell script | `echo "Script name: $0"` |

## Command-Line Arguments

| Variable | Description | Example Usage |
|----------|-------------|---------------|
| `$1`, `$2`, ... | Positional parameters (individual arguments) | `echo "First arg: $1"` |
| `$#` | Number of positional parameters | `echo "Argument count: $#"` |
| `$*` | All positional parameters as a single word | `echo "All args: $*"` |
| `$@` | All positional parameters as separate words | `for arg in "$@"; do echo "$arg"; done` |

## Special Parameter Behavior

### `$*` vs `$@`

- `"$*"` expands to a single string with parameters joined by the first character of `IFS` (usually a space)
- `"$@"` expands to separate strings for each parameter, preserving spaces within arguments

```bash
# Assume IFS is space
set -- "arg with spaces" "another arg"

# $* treats all args as one string with spaces
for arg in "$*"; do
    echo "[$arg]"
done
# Output: [arg with spaces another arg]

# $@ preserves each argument as separate
for arg in "$@"; do
    echo "[$arg]"
done
# Output:
# [arg with spaces]
# [another arg]
```

### `$?` Exit Status

The exit status variable `$?` contains the return value of the last executed command:
- `0` typically indicates success
- Values `1-255` indicate various error conditions

```bash
# Test if a file exists
if [ -f /etc/passwd ]; then
    echo "File exists"
else
    echo "File does not exist"
fi
echo "Exit status of test: $?"  # Will be 0 if file exists, 1 if not
```

### `$$` Process ID

The current shell's process ID is useful for creating unique temporary files:

```bash
# Create a unique temporary file
TEMPFILE="/tmp/myapp.$$"
echo "Data" > "$TEMPFILE"
# Process the file
rm "$TEMPFILE"  # Clean up
```

### `$!` Background Process ID

Contains the process ID of the most recent background command:

```bash
# Start a background process and capture its PID
sleep 30 &
BG_PID=$!
echo "Background process ID: $BG_PID"

# Check if the process is still running
if kill -0 $BG_PID 2>/dev/null; then
    echo "Process is still running"
fi

# Kill the background process if needed
kill $BG_PID
```

## Parameter Expansion and Default Values

Special parameters can be used with parameter expansion modifiers:

| Syntax | Description | Example |
|--------|-------------|---------|
| `${param:-default}` | Use default value if param is unset or null | `${1:-"default value"}` |
| `${param:=default}` | Assign default value if param is unset or null | `${count:=0}` |
| `${param:?message}` | Display error if param is unset or null | `${required_param:?"Missing parameter"}` |
| `${param:+alternate}` | Use alternate value if param is set and not null | `${optional:+"is set"}` |
| `${#param}` | Length of the param value | `${#1}` (length of first argument) |

## Implementation in psh

In psh, these special variables are implemented in the shell context and maintained throughout execution:

1. Process variables are updated when processes start/stop
2. Argument variables are updated when functions or scripts are called
3. The shell tracks exit status after each command completes

Special variables should be treated as read-only (except when explicitly setting positional parameters with `set`).

## Practical Examples

### Script Argument Handling

```bash
#!/usr/bin/env psh
# Check if required argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <filename>" >&2
    exit 1
fi

# Use first argument as filename
FILENAME="$1"
echo "Processing $FILENAME..."

# Process all additional arguments
shift
echo "Additional arguments: $#"
for arg in "$@"; do
    echo "- $arg"
done
```

### Error Handling

```bash
#!/usr/bin/env psh
# Run a command and check its exit status
grep "pattern" datafile
if [ $? -ne 0 ]; then
    echo "Pattern not found in datafile" >&2
    exit 1
fi

# Alternative approach with direct conditional
if ! grep "pattern" datafile; then
    echo "Pattern not found in datafile" >&2
    exit 1
fi
```

### Background Process Management

```bash
#!/usr/bin/env psh
# Start background process
echo "Starting background process..."
sleep 30 &
PID=$!
echo "Process ID: $PID"

# Do other work
echo "Doing other work while process runs..."
sleep 2

# Check if background process is still running
if kill -0 $PID 2>/dev/null; then
    echo "Background process is still running."
    kill $PID
    echo "Process terminated."
fi
```

### PID in Filename

```bash
#!/usr/bin/env psh
# Create unique log file using process ID
LOGFILE="/tmp/logfile.$$"
echo "Starting logging to $LOGFILE"
echo "Log started at $(date)" > "$LOGFILE"

# Cleanup trap to remove log file on exit
trap "rm -f $LOGFILE; echo 'Log file removed'" EXIT

# Do some work
echo "Doing work..." >> "$LOGFILE"
sleep 2
echo "Work complete" >> "$LOGFILE"

echo "Log contents:"
cat "$LOGFILE"
# File will be automatically removed by trap when script exits
```

## Best Practices

1. Always quote special parameters when expanding them: `"$@"`, `"$1"`, etc.
2. Check argument count (`$#`) before accessing specific positional parameters
3. Use `${var:-default}` to provide default values for optional parameters
4. Save `$?` immediately after a command if you need to use it later
5. Use `$$` to create unique temporary files or directories
6. Check exit status with `if` directly rather than comparing `$?` when possible
7. Prefer `"$@"` over `"$*"` when processing all arguments to preserve spaces