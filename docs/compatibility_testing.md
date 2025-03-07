# Python Shell Compatibility Testing Framework

The Python Shell (psh) includes a comprehensive testing framework for ensuring compatibility with bash. This document explains how the framework works and how to use it to test shell compatibility.

## Overview

The compatibility testing framework provides tools for running the same commands in both `psh` and `bash`, then comparing their outputs to ensure they behave the same way. This approach verifies that scripts written for bash will work correctly with `psh`.

## Framework Components

### Core Components

#### `ShellCompatibilityTester`

The main class that orchestrates compatibility testing:

```python
tester = ShellCompatibilityTester()
tester.assert_outputs_match("echo 'Hello, World!'")
```

This class provides methods for:
- Running commands in psh and bash
- Comparing stdout, stderr, and exit codes
- Generating detailed diffs when outputs don't match
- Creating isolated test environments

#### `CommandResult`

A data class that captures the result of running a command:

```python
class CommandResult:
    stdout: str     # Standard output
    stderr: str     # Standard error
    exit_code: int  # Exit status code
```

#### Helper Functions

- `create_compatibility_test`: Creates a test function for a single command
- `create_multi_command_test`: Creates a test function for multiple commands

## Test Organization

Compatibility tests are organized in the `tests/compatibility/` directory:

```
tests/compatibility/
├── __init__.py               # Package exports
├── framework.py              # Core testing framework
├── test_basic.py             # Basic commands and features
├── test_control_structures.py # Control structure tests
└── README.md                 # Framework documentation
```

## Writing Compatibility Tests

### Direct API Usage

The simplest way to create a test is to use the API directly:

```python
def test_echo_command(self):
    """Test basic echo command."""
    tester = ShellCompatibilityTester()
    tester.assert_outputs_match("echo 'Hello, World!'")
```

### Class-Based Tests

For organizing related tests:

```python
class TestBasicCommands:
    """Test basic shell command compatibility."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_variable_expansion(self):
        """Test variable expansion."""
        self.tester.assert_outputs_match("""
        export MSG='Hello'
        echo $MSG
        """)
```

### Test Factory Functions

For creating tests programmatically:

```python
# Create a test function automatically
test_echo = create_compatibility_test("echo 'Factory test'")

# Create a multi-command test
test_script = create_multi_command_test([
    "echo 'Step 1' > file.txt",
    "cat file.txt",
    "rm file.txt"
])
```

### Parameterized Tests

For testing many similar commands:

```python
@pytest.mark.parametrize("command", [
    "echo 'test 1'",
    "echo 'test 2' | grep test",
    "ls -la | head -n 5",
])
def test_parameterized(command):
    tester = ShellCompatibilityTester()
    tester.assert_outputs_match(command)
```

## Test Configuration Options

When comparing outputs, the framework provides several options:

```python
tester.assert_outputs_match(
    command,
    env={"VAR": "value"},        # Set environment variables
    ignore_exit_code=True,       # Ignore differences in exit codes
    ignore_stderr=True,          # Ignore differences in stderr
    normalize_whitespace=True,   # Normalize whitespace before comparing
    ignore_empty_lines=True      # Ignore empty lines in output
)
```

## Handling Shell Differences

Sometimes there are legitimate differences between shells. The framework provides options to handle these:

1. **Environment Variables**: Set specific variables for testing
2. **Whitespace Normalization**: Handle formatting differences
3. **Exit Code Handling**: Optionally ignore exit code differences
4. **Error Output Filtering**: Ignore differences in error messages
5. **File Path Handling**: Use absolute paths in tests for reliability

## Test Environment

The framework creates isolated test environments to ensure tests don't interfere with each other:

1. **Temporary Files**: Tests using files create them in temporary locations
2. **Shell History**: Shell history is disabled during tests
3. **Working Directory**: Tests run in isolated directories

## Common Testing Patterns

### Testing Variable Expansion

```python
def test_variable_expansion(self):
    self.tester.assert_outputs_match("""
    export MSG='Hello'
    echo $MSG
    """)
```

### Testing Redirection

```python
def test_output_redirection(self):
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
        temp_path = temp_file.name
        
    try:
        cmd = f"""
        echo 'test output' > {temp_path}
        cat {temp_path}
        """
        self.tester.assert_outputs_match(cmd)
    finally:
        os.unlink(temp_path)
```

### Testing Control Structures

```python
def test_if_statement(self):
    self.tester.assert_outputs_match("""
    if true; then
        echo 'True branch'
    else
        echo 'False branch'
    fi
    """)
```

### Testing Exit Status

```python
def test_exit_status(self):
    self.tester.assert_outputs_match("""
    false
    echo $?
    """)
```

## Running the Tests

Run the compatibility tests with pytest:

```bash
# Run all compatibility tests
pytest tests/compatibility/

# Run specific test file
pytest tests/compatibility/test_basic.py

# Run a specific test
pytest tests/compatibility/test_basic.py::TestQuoting::test_double_quotes
```

## Troubleshooting and Best Practices

1. **Use Raw Strings**: For escape sequences in test strings
   ```python
   tester.assert_outputs_match(r'echo "Escaped: \$HOME"')
   ```

2. **Use Multiline Strings**: For commands with multiple lines
   ```python
   tester.assert_outputs_match("""
   echo 'line 1'
   echo 'line 2'
   """)
   ```

3. **Temporary Files**: For file operations, use temporary files with absolute paths
   ```python
   with tempfile.NamedTemporaryFile() as tmp:
       tester.assert_outputs_match(f"echo 'data' > {tmp.name}")
   ```

4. **Isolate Variables**: Use unique variable names in tests to avoid conflicts

5. **Test One Feature**: Each test should focus on testing one specific feature or behavior

## Expanding Test Coverage

When adding new shell features, create corresponding compatibility tests to ensure they work as expected. Areas to test include:

1. Command execution and pipelines
2. Variable assignment and expansion
3. Quoting and escaping
4. Redirection and file operations
5. Control structures (if, for, while, case)
6. Exit status and error handling
7. Command substitution
8. Wildcards and pattern matching
9. Built-in commands
10. Script execution

## Conclusion

The compatibility testing framework provides a powerful way to ensure `psh` works consistently with `bash`. By systematically comparing behaviors, we can identify and fix compatibility issues, making `psh` a more reliable alternative to traditional shells.