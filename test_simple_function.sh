#\!/usr/bin/env python3 -m src.shell

# Define a simple function
function hello() {
    echo "Hello world\!"
}

# Call the function
hello

# Function with args
function greet() {
    echo "Hello, $1\!"
}

# Call with argument
greet "User"

echo "Done\!"
