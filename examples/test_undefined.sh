#!/usr/bin/env psh
# Test script for undefined variables in arithmetic expressions

echo "Testing arithmetic with undefined variables:"
echo "1. Basic undefined variable: $((undefined))"
echo "2. Undefined variable plus number: $((undefined + 5))"
echo "3. Multiple undefined variables: $((undefined1 + undefined2))"
echo "4. Complex expression: $((undefined1 * undefined2 + 10))"
echo "5. Nested expressions: $((1 + $((undefined * 3))))"

# Setting a variable for comparison
DEFINED=10
echo "6. Comparing defined vs undefined: $((DEFINED + undefined))"