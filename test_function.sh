#!/usr/bin/env python3 -m src.shell
# Test script for multiline functions

# Define a simple multiline function
function greet() {
    echo "Hello, $1!"
    echo "Nice to meet you."
}

# Call the function
greet "World"

echo "Script completed successfully!"