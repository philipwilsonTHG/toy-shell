#!/usr/bin/env psh

# This is an example script demonstrating control structures
# Run with: psh examples/control_structures.sh

# Set some variables
count=5
name="world"

# If statement
if test -f /etc/passwd; then
    echo "System has password file"
else
    echo "No password file found"
fi

# For loop
echo "Counting from 1 to $count:"
for i in 1 2 3 4 5; do
    echo "Number: $i"
done

# While loop
echo "Counting down from $count to 1:"
while test $count -gt 0; do
    echo "Countdown: $count"
    count=$(($count - 1))
done

# Until loop
count=1
echo "Counting up until 5:"
until test $count -gt 5; do
    echo "Count up: $count"
    count=$(($count + 1))
done

# Case statement
echo "Testing case statement with value: $name"
case $name in
    world)
        echo "Hello, world!"
        ;;
    user)
        echo "Hello, user!"
        ;;
    *)
        echo "Hello, unknown person!"
        ;;
esac

# Function definition
function greet() {
    echo "Greeting: Hello, $1!"
}

# Function call
greet "friend"
greet "neighbor"

echo "Script completed successfully!"