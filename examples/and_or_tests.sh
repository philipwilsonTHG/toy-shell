#!/usr/bin/env psh
# Tests for AND-OR list implementation

# Basic AND and OR examples
echo "=== Basic AND-OR Tests ==="
echo "Test 1: true && echo 'AND success'"
true && echo "AND success"

echo "Test 2: false && echo 'AND failure (should not print)'"
false && echo "AND failure (should not print)"

echo "Test 3: false || echo 'OR success'"
false || echo "OR success"

echo "Test 4: true || echo 'OR failure (should not print)'"
true || echo "OR failure (should not print)"

# Complex chaining
echo -e "\n=== Complex Chaining Tests ==="
echo "Test 5: true && echo 'One' && echo 'Two'"
true && echo "One" && echo "Two"

echo "Test 6: true && false && echo 'Three (should not print)'"
true && false && echo "Three (should not print)"

echo "Test 7: false || echo 'Four' || echo 'Five (should print, but not this one)'"
false || echo "Four" || echo "Five (should print, but not this one)"

echo "Test 8: false && echo 'Six (should not print)' || echo 'Seven (should print)'"
false && echo "Six (should not print)" || echo "Seven (should print)"

echo "Test 9: true || echo 'Eight (should not print)' && echo 'Nine (should not print)'"
true || echo "Eight (should not print)" && echo "Nine (should not print)"

# Command sequences
echo -e "\n=== Command Sequences ==="
echo "Test 10: echo 'A'; echo 'B' && echo 'C'"
echo "A"; echo "B" && echo "C"

echo "Test 11: (echo 'D' && echo 'E') || echo 'F (should not print)'"
echo "D" && echo "E" || echo "F (should not print)"

echo "Test 12: Exit status examples"
echo "Using exit status from previous command. 'grep' will fail:"
grep "nonexistent" and_or_tests.sh && echo "Should not print" || echo "grep failed with status $?"