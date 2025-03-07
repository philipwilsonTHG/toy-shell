#!/usr/bin/env python3
"""
Compatibility tests for shell control structures.

These tests verify that psh executes control structures (if, for, while, case)
identically to bash.
"""

import pytest
from .framework import ShellCompatibilityTester


class TestIfStatements:
    """Test if statement compatibility between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_simple_if(self):
        """Test simple if statement."""
        cmd = """
        if true; then
            echo 'True branch'
        else
            echo 'False branch'
        fi
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_if_else(self):
        """Test if-else statement."""
        cmd = """
        if false; then
            echo 'True branch'
        else
            echo 'False branch'
        fi
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_if_elif_else(self):
        """Test if-elif-else statement."""
        cmd = """
        x=2
        if [ $x -eq 1 ]; then
            echo 'x is 1'
        elif [ $x -eq 2 ]; then
            echo 'x is 2'
        else
            echo 'x is something else'
        fi
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_nested_if(self):
        """Test nested if statements."""
        cmd = """
        x=2
        y=3
        if [ $x -eq 2 ]; then
            if [ $y -eq 3 ]; then
                echo 'x is 2 and y is 3'
            fi
        fi
        """
        self.tester.assert_outputs_match(cmd)


class TestLoops:
    """Test loop compatibility between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_for_loop(self):
        """Test for loop execution."""
        cmd = """
        for i in 1 2 3; do 
            echo $i
        done
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_while_loop(self):
        """Test while loop execution."""
        cmd = """
        count=0
        while [ $count -lt 3 ]; do
            echo $count
            count=$((count + 1))
        done
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_until_loop(self):
        """Test until loop execution."""
        cmd = """
        count=0
        until [ $count -ge 3 ]; do
            echo $count
            count=$((count + 1))
        done
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_nested_loops(self):
        """Test nested loops."""
        cmd = """
        for i in 1 2; do
            for j in a b; do
                echo "$i-$j"
            done
        done
        """
        self.tester.assert_outputs_match(cmd)


class TestCaseStatements:
    """Test case statement compatibility between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
    
    def test_simple_case(self):
        """Test simple case statement."""
        cmd = """
        val="apple"
        case $val in
            orange)
                echo "It's an orange"
                ;;
            apple)
                echo "It's an apple"
                ;;
            *)
                echo "Unknown fruit"
                ;;
        esac
        """
        self.tester.assert_outputs_match(cmd)
    
    def test_case_with_patterns(self):
        """Test case statement with pattern matching."""
        cmd = """
        val="file.txt"
        case $val in
            *.txt)
                echo "Text file"
                ;;
            *.jpg|*.png)
                echo "Image file"
                ;;
            *)
                echo "Unknown file type"
                ;;
        esac
        """
        self.tester.assert_outputs_match(cmd)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])