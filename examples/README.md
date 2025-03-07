# Shell Examples

This directory contains example scripts for the Python Shell (psh).

## Debug Example

The `debug_example.sh` script demonstrates the AST debugging feature. It includes:
- Simple commands
- If-else statements
- For loops
- While loops
- Case statements

Run it with the `--debug` flag to see the AST before execution:

```
psh --debug examples/debug_example.sh
```

## For Loop Example

The `for_loop.sh` script shows a simple for loop example.

Run it with:

```
psh examples/for_loop.sh
```

## Arithmetic Expansion Example

The `arithmetic.sh` script demonstrates the arithmetic expansion feature using the `$(( expression ))` syntax. It includes:
- Basic arithmetic operations
- Variable usage in expressions
- Operator precedence
- Logical operators
- Comparison operators
- Ternary operator
- Nested arithmetic expressions
- Using arithmetic in control structures
- A factorial calculation example

Run it with:

```
psh examples/arithmetic.sh
```