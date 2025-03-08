# Case Statement Usage in Python Shell (psh)

## Overview

This document outlines how to use case statements in psh (Python Shell) and describes the current implementation, limitations, and recommended usage patterns.

## Case Statement Structure

Case statements in psh follow the same structure as in bash:

```bash
case WORD in
    PATTERN1)
        COMMANDS1
        ;;
    PATTERN2)
        COMMANDS2
        ;;
    *)
        DEFAULT_COMMANDS
        ;;
esac
```

Where:
- `WORD` is the value to match against patterns (can be a variable or string)
- `PATTERN` can be a literal string or a glob pattern (e.g., `*.txt`)
- Multiple patterns can be separated by the pipe (`|`) character
- Commands are executed for the first matching pattern
- The `*` pattern acts as a default/catch-all case

## Improved Pattern Matching

psh supports the following pattern matching features:

1. **Simple literal matching**: `case $var in apple) ... ;; esac`
2. **Multiple pattern alternatives**: `case $var in apple|orange|pear) ... ;; esac`
3. **Glob-style wildcard patterns**: `case $filename in *.txt) ... ;; esac`
4. **Default case with asterisk**: `case $var in *) ... ;; esac`

## Current Limitations

The case statement implementation has the following limitations:

1. **Script Execution**: Case statements work best when used interactively or when a script is sourced rather than executed as a file argument. There are known issues with parsing case statements in script files passed as arguments to psh.

2. **Compound Patterns**: Some complex pattern combinations might not be parsed correctly.

3. **Nested Structures**: Avoid nesting case statements within each other for best compatibility.

## Recommended Usage

For the most reliable case statement operation, we recommend:

1. **Use case statements in functions**: Wrap case statements in functions as shown in the examples.

2. **Source scripts rather than executing them**: Use `source script.sh` or `. script.sh` instead of running `psh script.sh`.

3. **Keep patterns simple**: Use basic patterns and avoid nested case statements.

4. **Test thoroughly**: Always test your case statements in the context they will be used.

## Examples

See `examples/case_demo.sh` for a comprehensive demonstration of case statements in psh.

Run the demo with:

```bash
psh -c "source examples/case_demo.sh"
```

## Future Improvements

The psh development team is working on the following improvements:

1. Better handling of case statements in script execution mode
2. Support for more complex pattern matching
3. Performance optimizations for large case statements
4. Improved error reporting for malformed case statements

## Reporting Issues

If you encounter problems with case statements in psh, please report them on our issue tracker with a minimal example that reproduces the issue.