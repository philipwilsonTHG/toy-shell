# POSIX-Compatible Test Command Implementation in psh

## Overview

The psh shell includes a fully POSIX-compliant implementation of the `test` and `[` builtin commands. These commands evaluate expressions and return success (0) or failure (1) based on the result, allowing them to be used in conditional constructs like `if` statements.

## Implementation Details

### Command Structure

The `test` command is implemented in `/src/builtins/test.py` with the following features:

- Support for both `test` and `[` command forms
- Proper exit code handling (0 for true, 1 for false, 2 for errors)
- Full expression parser with correct operator precedence
- Short-circuit evaluation for logical operators
- Comprehensive error handling

### File Tests

| Operator | Description | Implementation |
|----------|-------------|----------------|
| `-e file` | True if file exists | `os.path.exists(file)` |
| `-f file` | True if file exists and is a regular file | `os.path.isfile(file)` |
| `-d file` | True if file exists and is a directory | `os.path.isdir(file)` |
| `-r file` | True if file exists and is readable | `os.access(file, os.R_OK)` |
| `-w file` | True if file exists and is writable | `os.access(file, os.W_OK)` |
| `-x file` | True if file exists and is executable | `os.access(file, os.X_OK)` |
| `-s file` | True if file exists and has a size greater than zero | `os.path.exists(file) and os.path.getsize(file) > 0` |
| `-L file` | True if file exists and is a symbolic link | `os.path.islink(file)` |
| `-b file` | True if file exists and is a block special file | Platform-specific implementation |
| `-c file` | True if file exists and is a character special file | Platform-specific implementation |
| `-g file` | True if file exists and its set-group-ID bit is set | Permission check with `os.stat` |
| `-u file` | True if file exists and its set-user-ID bit is set | Permission check with `os.stat` |
| `-G file` | True if file exists and its group ID matches the effective group ID | Group ID check with `os.stat` |
| `-O file` | True if file exists and its owner matches the effective user ID | Owner check with `os.stat` |
| `-S file` | True if file exists and is a socket | Special file type check |
| `-p file` | True if file exists and is a named pipe (FIFO) | Special file type check |
| `-t fd` | True if file descriptor is open and refers to a terminal | Terminal check with special handling |

### String Tests

| Operator | Description | Implementation |
|----------|-------------|----------------|
| `-z string` | True if the length of string is zero | `len(string) == 0` |
| `-n string` | True if the length of string is non-zero | `len(string) > 0` |
| `s1 = s2` | True if the strings s1 and s2 are identical | `s1 == s2` |
| `s1 == s2` | Same as `s1 = s2` (added for compatibility) | `s1 == s2` |
| `s1 != s2` | True if the strings s1 and s2 are not identical | `s1 != s2` |
| `s1 < s2` | True if string s1 comes before s2 in lexicographical order | Lexicographical comparison |
| `s1 > s2` | True if string s1 comes after s2 in lexicographical order | Lexicographical comparison |

### Integer Comparisons

| Operator | Description | Implementation |
|----------|-------------|----------------|
| `n1 -eq n2` | True if the integers n1 and n2 are algebraically equal | `n1 == n2` |
| `n1 -ne n2` | True if the integers n1 and n2 are not algebraically equal | `n1 != n2` |
| `n1 -gt n2` | True if the integer n1 is algebraically greater than n2 | `n1 > n2` |
| `n1 -ge n2` | True if the integer n1 is algebraically greater than or equal to n2 | `n1 >= n2` |
| `n1 -lt n2` | True if the integer n1 is algebraically less than n2 | `n1 < n2` |
| `n1 -le n2` | True if the integer n1 is algebraically less than or equal to n2 | `n1 <= n2` |

### Logical Operators

| Operator | Description | Implementation |
|----------|-------------|----------------|
| `!` | Unary negation operator - inverts the exit status | `not expr` |
| `-a` | Binary AND operator - true if both expressions are true | `expr1 and expr2` with short-circuit evaluation |
| `-o` | Binary OR operator - true if either expression is true | `expr1 or expr2` with short-circuit evaluation |
| `( expr )` | Parentheses for grouping expressions | Recursive evaluation of grouped expression |

### Special Cases

The implementation handles several special POSIX requirements:

1. **Empty expression**: `test` with no arguments returns false (1)
2. **Single argument**: `test arg` returns true (0) if `arg` is non-empty
3. **Context-sensitive operators**: `-a` and `-o` are treated as strings in some contexts
4. **Missing closing bracket**: Proper error handling for `[` without matching `]`
5. **Four-argument special case**: `test arg1 op arg2` when operator is a relational or equality operator

## Expression Evaluation

The command implements a recursive descent parser with proper operator precedence:

1. **Highest precedence**: Parentheses for grouping
2. **Second highest**: Negation (`!`)
3. **Third highest**: Binary AND (`-a`)
4. **Lowest precedence**: Binary OR (`-o`)

Short-circuit evaluation is implemented to match POSIX requirements, improving performance by avoiding unnecessary evaluations.

## Usage Examples

```bash
# Basic file tests
if test -f "/path/to/file"; then
    echo "File exists and is a regular file"
fi

# File tests with [
if [ -d "/path/to/directory" -a -r "/path/to/directory" ]; then
    echo "Directory exists and is readable"
fi

# String comparison
if [ "$string1" = "$string2" ]; then
    echo "Strings are equal"
fi

# Integer comparison
if [ "$count" -gt 10 ]; then
    echo "Count is greater than 10"
fi

# Complex expressions with grouping
if [ \( "$a" = "$b" -o "$a" = "$c" \) -a "$d" = "$e" ]; then
    echo "Complex condition is true"
fi
```

## Error Handling

The implementation follows POSIX error handling requirements:

- Syntax errors in expressions return exit code 2
- Appropriate error messages on stderr
- Correct handling of malformed expressions
- Type checking for integer operations