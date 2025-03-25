#!/usr/bin/env psh

# Test if statements in different formats

# Single-line format (works)
echo "Testing single-line if statement:"
if true; then echo "Single-line if statement works"; fi

# Multi-line format (now fixed!)
echo "Testing multi-line if statement:"
if true
then
    echo "Multi-line if statement works"
fi

# Single-line with else (works)
echo "Testing single-line if-else statement:"
if false; then echo "Should not see this"; else echo "Single-line if-else works"; fi

# Multi-line with else (now fixed!)
echo "Testing multi-line if-else statement:"
if false
then
    echo "Should not see this"
else
    echo "Multi-line if-else works"
fi

# Multi-line with elif (now fixed!)
echo "Testing multi-line if-elif-else statement:"
if false
then
    echo "Should not see this (if)"
elif true
then
    echo "Multi-line elif works"
else
    echo "Should not see this (else)"
fi

# Multi-line nested if statements (now fixed!)
echo "Testing nested multi-line if statements:"
if true
then
    echo "Outer if is true"
    if true
    then
        echo "Inner if is true too"
    fi
fi

# Test complex conditions with multi-line
echo "Testing multi-line if with complex condition:"
if [ 1 -eq 1 ] && [ 2 -eq 2 ]
then
    echo "Complex condition works"
fi

echo "Test completed successfully"