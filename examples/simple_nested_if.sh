#!/usr/bin/env psh
echo "Start"
if true; then
    echo "Outer if"
    if true; then
        echo "Inner if"
    fi
fi
echo "End"