#!/usr/bin/env psh
# Test script for nested if statements

# Simple if statement spanning multiple lines
if true
then
    echo "Outer if - True branch executed"
    
    # Nested if statement inside the true branch
    if true
    then
        echo "Nested if - True branch executed"
    else
        echo "Nested if - False branch executed"
    fi
    
    echo "After nested if"
else
    echo "Outer if - False branch executed"
fi

echo "Script completed successfully"

# Test with deeper nesting
if true
then
    echo "Level 1 - True"
    if true
    then
        echo "Level 2 - True"
        if false
        then
            echo "Level 3 - True (should not print)"
        else
            echo "Level 3 - False"
            if true
            then
                echo "Level 4 - True"
            fi
        fi
    fi
fi

echo "Deep nesting completed"