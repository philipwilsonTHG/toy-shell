#!/usr/bin/env bash

# Test variable expansion with the new state machine expander

# Basic variable expansion
echo "=== Basic Variable Expansion ==="
name="World"
echo "Hello, $name"

# Arithmetic expansion
echo "=== Arithmetic Expansion ==="
x=5
y=10
echo "Sum: $((x + y))"
echo "Product: $((x * y))"
echo "Complex: $(( (x + y) * 2 ))"

# Brace expansion
echo "=== Brace Expansion ==="
echo "Numbers: {1..5}"
echo "Letters: {a..e}"

# Quoted strings
echo "=== Quoted Strings ==="
echo 'Single quoted: $name'  # Should not expand
echo "Double quoted: $name"  # Should expand
echo "Mixed \"quotes\" in string"

# Special variables
echo "=== Special Variables ==="
echo "Exit status: $?"

# A complex example combining multiple features
echo "=== Complex Example ==="
count=3
echo "Counting to $count: $((count+1)) $((count+2)) $((count+3))"
echo "File list: {*.py,*.sh}"

echo "=== Test completed successfully ==="