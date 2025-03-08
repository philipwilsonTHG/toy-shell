#!/usr/bin/env python3 -m src.shell
# Test script for multiline functions with arguments

# Define a multiline function with positional arguments
function greet_person() {
    echo "Hello, $1!"
    echo "You are $2 years old."
    echo "You live in $3."
}

# Call the function with arguments
greet_person "Alice" "30" "New York"

# Call with different arguments
greet_person "Bob" "25" "San Francisco"

echo "Script completed successfully!"