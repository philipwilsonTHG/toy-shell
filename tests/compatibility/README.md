# Shell Compatibility Tests

This directory contains tests that compare the behavior of `psh` against `bash` to ensure compatibility.

## Overview

The compatibility tests verify that `psh` produces identical (or expected) output compared to `bash` for the same input commands. This approach helps identify behavioral differences and ensures that shell scripts written for bash will work correctly with `psh`.

## Test Framework

The compatibility testing framework (`compatibility_framework.py`) provides:

1. **Command Execution**: Run commands in both `psh` and `bash` shells
2. **Output Comparison**: Compare stdout, stderr, and exit codes
3. **Test Environment**: Create isolated test environments
4. **Normalization Options**: Control how outputs are compared (whitespace, empty lines)
5. **Detailed Diffs**: Generate clear diffs when outputs don't match

## Creating Compatibility Tests

Tests can be created in several ways:

### Direct API Usage

```python
def test_my_command():
    tester = ShellCompatibilityTester()
    tester.assert_outputs_match("echo 'Hello, World!'")
```

### Test Factory Functions

```python
# Create a test function automatically
test_echo = create_compatibility_test("echo 'Factory test'")
```

### Multi-Command Tests

```python
def test_script_behavior():
    commands = [
        "echo 'Step 1' > file.txt",
        "cat file.txt",
        "grep Step file.txt",
    ]
    setup_commands = ["mkdir -p test_dir"]
    
    tester = ShellCompatibilityTester()
    with tester.compatibility_test(commands, setup_commands):
        pass
```

### Parameterized Tests

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

## Handling Differences

Sometimes there are legitimate differences between shells. The framework provides options to handle these:

- `ignore_exit_code=True`: Ignore differences in exit codes
- `ignore_stderr=True`: Ignore differences in stderr output
- `normalize_whitespace=True`: Normalize whitespace before comparing
- `ignore_empty_lines=True`: Ignore empty lines in output

## Running Tests

Run the compatibility tests with pytest:

```bash
pytest tests/compatibility/
```

Or run a specific test file:

```bash
pytest tests/compatibility/test_builtins_compatibility.py
```