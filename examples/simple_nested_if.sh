#!/usr/bin/env psh
# Simplified test for nested if statements

# Simple if statement
if true
then
    echo "Outer if - True branch"
    if true
    then
        echo "Nested if - True branch"
    fi
fi

echo "Done"