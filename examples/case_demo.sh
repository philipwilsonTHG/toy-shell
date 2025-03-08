#!/usr/bin/env bash

#
# Case statement demonstration script for psh
# Use with: psh -c "source examples/case_demo.sh"
#

# Simple cases without functions for better compatibility
echo "Direct case statements:"
echo "---------------------"

# Simple case with a fixed value
VALUE="apple"
echo -n "Fruit type for $VALUE: "
case $VALUE in
    apple)
        echo "common fruit"
        ;;
    kiwi)
        echo "exotic fruit"
        ;;
    *)
        echo "unknown fruit"
        ;;
esac

# Simple case with file extension
FILENAME="document.txt"
echo -n "File type for $FILENAME: "
case $FILENAME in
    *.txt)
        echo "text file"
        ;;
    *.jpg)
        echo "image file"
        ;;
    *)
        echo "unknown file"
        ;;
esac
echo

# Multiple patterns in a case statement
echo "Case statement with multiple patterns:"
echo "----------------------------------"

# Test with animal types
ANIMAL="dog"
echo -n "The $ANIMAL has "
case $ANIMAL in
    horse | dog | cat)
        echo "four legs"
        ;;
    bird | chicken)
        echo "two legs and wings"
        ;;
    snake | worm)
        echo "no legs"
        ;;
    *)
        echo "an unknown number of legs"
        ;;
esac

# Test with car brands
CAR="toyota"
echo -n "The $CAR is "
case $CAR in
    bmw | audi | mercedes)
        echo "a German car"
        ;;
    toyota | honda | mazda)
        echo "a Japanese car"
        ;;
    ford | chevrolet)
        echo "an American car"
        ;;
    *)
        echo "a car from an unknown country"
        ;;
esac

# Default case demonstration
echo -n "Testing the default (*) pattern: "
UNKNOWN_VALUE="xyz123"
case $UNKNOWN_VALUE in
    [0-9]*)
        echo "starts with a number"
        ;;
    [A-Z]*)
        echo "starts with an uppercase letter"
        ;;
    *)
        echo "doesn't match any defined pattern"
        ;;
esac

echo
echo "Case statement demonstration complete."