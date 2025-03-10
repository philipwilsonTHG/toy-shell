# Semantic Differences: Interactive Input vs. Shell Scripts

## Input Processing
- **Interactive Mode**: Input is processed line-by-line, with immediate feedback
- **Script Mode**: Entire script is read before execution begins, enabling features like function definition before use
- **✅ Implemented**: Yes - psh handles both modes differently

## Variable Expansion
- **Interactive Mode**: Variables are expanded at the command line as typed
- **Script Mode**: Variables are expanded during script execution, allowing for different scope handling
- **✅ Implemented**: Yes - separate variable scopes for script execution

## Error Handling
- **Interactive Mode**: Errors display but shell continues running
- **Script Mode**: By default, scripts continue after errors, but can be made to exit on first error (set -e)
- **✅ Implemented**: Yes - `set -e` behavior works with proper exemptions for conditionals

## Job Control
- **Interactive Mode**: Full job control available (fg, bg, jobs)
- **Script Mode**: Limited job control by default
- **✅ Implemented**: Yes - job control only enabled in interactive mode

## Prompt Handling
- **Interactive Mode**: Displays PS1/PS2 prompts for user guidance
- **Script Mode**: No prompts displayed
- **✅ Implemented**: Yes - prompts only displayed in interactive mode

## Completion and History
- **Interactive Mode**: Command completion and history recall available
- **Script Mode**: No history or completion mechanisms
- **✅ Implemented**: Yes - completion and history only available in interactive

## Environment Inheritance
- **Interactive Mode**: Environment changes persist until shell exit
- **Script Mode**: Scripts run in subshell by default; environment changes don't propagate back to parent shell unless sourced (`. script.sh` or `source script.sh`)
- **✅ Implemented**: Yes - proper environment handling for both modes

## Signal Handling
- **Interactive Mode**: Interactive shells ignore SIGTERM, SIGINT handled specially
- **Script Mode**: Default signal handling leads to script termination
- **✅ Implemented**: Yes - different signal handlers for interactive and script modes

## Execution Context
- **Interactive Mode**: Commands are executed in the current shell process
- **Script Mode**: Scripts are typically executed in a separate subprocess
- **✅ Implemented**: Yes - different execution contexts for both modes

## Parsing Differences
- **Interactive Mode**: Commands can be edited before execution
- **Script Mode**: Entire script is parsed first, allowing detection of syntax errors before execution begins
- **✅ Implemented**: Yes - script syntax validation before execution

## Set Command Options
- **Interactive Mode**: Options can be set for the current session
- **Script Mode**: Options like `-e` (exit on error) and `-x` (print commands) are particularly useful
- **✅ Implemented**: Yes - `set -e` and `set -x` support in both modes

Understanding these differences is critical for implementing a shell that correctly handles both interactive and script execution modes. PSH now properly implements all of these semantic differences.