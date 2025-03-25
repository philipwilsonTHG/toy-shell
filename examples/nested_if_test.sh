#!/usr/bin/env psh

# Test nested if statements

echo "Testing nested if statements:"
if true
then
    echo "Outer if is true"
    if true
    then
        echo "Inner if is true too"
    fi
fi

echo "Test completed"