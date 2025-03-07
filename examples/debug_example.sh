#!/usr/bin/env psh

# Example script to demonstrate the AST debugging feature.
# Run with: psh --debug examples/debug_example.sh

# Simple command
echo "This is a simple command"

# Conditional
if [ -f /etc/hosts ]; then
    echo "The hosts file exists"
else
    echo "The hosts file does not exist"
fi

# For loop
for i in 1 2 3; do
    echo "Number: $i"
done

# While loop
#counter=3
#while [ $counter -gt 0 ]; do
#    echo "Countdown: $counter"
#    counter=$((counter - 1))
#done

# Case statement
animal="dog"
case $animal in
    cat) echo "Meow" ;;
    dog) echo "Woof" ;;
    *) echo "Unknown animal" ;;
esac

echo "All done!"
