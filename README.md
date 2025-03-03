# Python Shell (psh)

A feature-rich Unix shell implemented in Python with modern features and robust job control.

## Features

- Command execution with pipes and redirections
- Job control (bg, fg, jobs)
- Command history with search
- Environment variable management
- Command substitution $(command)
- Proper signal handling
- Configurable prompt
- Tab completion
- Shell scripting support

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/psh.git
cd psh

# Install in development mode
pip install -e .

# Or install directly
pip install .
```

Note: Python's readline module is used for command line editing and history. On Linux systems, this is typically provided by GNU readline. On macOS, it uses libedit. Make sure you have the appropriate system package installed:
- Linux (Debian/Ubuntu): `sudo apt-get install libreadline-dev`
- Linux (RHEL/Fedora): `sudo dnf install readline-devel`
- macOS: Already included with system Python

## Usage

```bash
# Interactive mode
psh

# Run script
psh script.sh
```

## Shell Features

### Job Control
```bash
command &          # Run in background
jobs              # List jobs
bg %N             # Resume job N in background
fg %N             # Bring job N to foreground
Ctrl+Z            # Stop current job
```

### History
```bash
history           # Show command history
history N         # Show last N commands
history -c        # Clear history
history -d N      # Delete history entry N
Ctrl+R            # Search history backward
Ctrl+S            # Search history forward
```

### Environment Variables
```bash
export            # List all variables
export VAR=value  # Set variable
unset VAR         # Remove variable
echo $VAR         # Use variable
echo ${VAR}       # Use variable (alternative)
```

### Command Substitution
```bash
echo "Date: $(date)"
files=$(ls)
path=$(pwd)/file
```

### Redirections
```bash
command > file    # Redirect output
command >> file   # Append output
command < file    # Redirect input
command 2> file   # Redirect error
command 2>&1      # Redirect error to output
```

### Pipes
```bash
command1 | command2 | command3
```

### Line Editing
- Arrow Keys: Navigate and browse history
  - Up/Down: Previous/next history entry
  - Left/Right: Move cursor position
- Keyboard Shortcuts:
  - Ctrl+P/Ctrl+N: Previous/next history (same as Up/Down)
  - Ctrl+F/Ctrl+B: Forward/backward char (same as Right/Left)
  - Alt+P/Alt+N: Search history backward/forward with prefix
  - Ctrl+A: Move to beginning of line
  - Ctrl+E: Move to end of line
  - Ctrl+K: Kill to end of line
  - Ctrl+U: Kill whole line
  - Ctrl+W: Kill word backward
  - Ctrl+Y: Yank killed text
  - Ctrl+R: Search history backward
  - Ctrl+S: Search history forward

## Configuration

The shell can be configured through ~/.pshrc:

```bash
# Example configuration
export PATH=$HOME/bin:$PATH
export EDITOR=vim
prompt_template="{user}@{host}:{cwd}$ "
histsize=10000
histfile="~/.psh_history"
debug=false
```

## Project Structure

```
src/
├── __init__.py
├── builtins/           # Built-in shell commands
│   ├── __init__.py
│   ├── core.py         # Core commands (cd, exit, etc.)
│   ├── env.py          # Environment variable management
│   ├── eval.py         # Command evaluation
│   ├── history.py      # History management
│   └── jobs.py         # Job control commands
├── config/             # Configuration management
│   ├── __init__.py
│   └── manager.py      # Config parsing and handling
├── context.py          # Global shell context
├── execution/          # Command execution
│   ├── __init__.py
│   ├── job_manager.py  # Job control and management
│   └── pipeline.py     # Pipeline execution
├── parser/             # Command parsing
│   ├── __init__.py
│   ├── expander.py     # Variable/command expansion
│   ├── lexer.py        # Command tokenization
│   └── quotes.py       # Quote handling
├── shell.py            # Main shell implementation
└── utils/              # Utility functions
    ├── __init__.py
    ├── completion.py   # Tab completion
    ├── history.py      # History utilities
    └── terminal.py     # Terminal control
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src

# Linting
pylint src
```

## License

MIT License - see LICENSE file for details.