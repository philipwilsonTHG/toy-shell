#!/usr/bin/env bash
# Example of arithmetic expansion in psh
# Run with: psh arithmetic.sh

echo "Arithmetic expansion examples:"
echo "----------------------------"

# Basic operations
echo "1 + 2 = $(( 1 + 2 ))"
echo "5 - 3 = $(( 5 - 3 ))"
echo "4 * 3 = $(( 4 * 3 ))"
echo "10 / 2 = $(( 10 / 2 ))"
echo "10 % 3 = $(( 10 % 3 ))"
echo "2 ** 3 = $(( 2 ** 3 ))"
echo

# Using variables
x=10
y=5
echo "x = $x, y = $y"
echo "x + y = $(( x + y ))"
echo "x - y = $(( x - y ))"
echo "x * y = $(( x * y ))"
echo "x / y = $(( x / y ))"
echo

# Operator precedence
echo "1 + 2 * 3 = $(( 1 + 2 * 3 ))"
echo "(1 + 2) * 3 = $(( (1 + 2) * 3 ))"
echo

# Logical operators
echo "Logical operators (1 = true, 0 = false):"
echo "1 && 1 = $(( 1 && 1 ))"
echo "1 && 0 = $(( 1 && 0 ))"
echo "1 || 0 = $(( 1 || 0 ))"
echo "0 || 0 = $(( 0 || 0 ))"
echo "!1 = $(( !1 ))"
echo "!0 = $(( !0 ))"
echo

# Comparison operators
echo "Comparison operators:"
echo "5 > 3 = $(( 5 > 3 ))"
echo "5 < 3 = $(( 5 < 3 ))"
echo "5 >= 5 = $(( 5 >= 5 ))"
echo "5 <= 4 = $(( 5 <= 4 ))"
echo "5 == 5 = $(( 5 == 5 ))"
echo "5 != 5 = $(( 5 != 5 ))"
echo

# Ternary operator
echo "Ternary operator examples:"
echo "x > y ? x : y = $(( x > y ? x : y ))"
echo "x < y ? x : y = $(( x < y ? x : y ))"
echo

# Nested arithmetic expressions
echo "Nested expressions:"
echo "1 + (2 * 3) = $(( 1 + (2 * 3) ))"
echo "1 + $(( 2 * 3 )) = $(( 1 + $(( 2 * 3 )) ))"
echo

# Using in control structures
echo "Using in while loop:"
i=1
while (( i <= 5 )); do
    echo "  Count: $i"
    i=$(( i + 1 ))
done
echo

# Calculating factorial (to demonstrate more complex usage)
calculate_factorial() {
    n=$1
    result=1
    
    while (( n > 0 )); do
        result=$(( result * n ))
        n=$(( n - 1 ))
    done
    
    echo "Factorial of $1 is $result"
}

echo "Calculating factorials:"
calculate_factorial 5
calculate_factorial 7

echo "Arithmetic expansion examples complete."