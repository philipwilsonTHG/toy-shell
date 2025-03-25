#!/usr/bin/env psh

# Test multi-line loops

# Multi-line while loop
echo "Testing multi-line while loop:"
count=3
while [ $count -gt 0 ]
do
    echo "Count: $count"
    count=$(($count - 1))
done

# Multi-line for loop
echo -e "\nTesting multi-line for loop:"
for i in 1 2 3
do
    echo "Iteration: $i"
done

echo "Test completed"