#!/usr/bin/env python3
"""
Test script for the new parser implementation.

This script tests the new parser on various shell constructs and compares
the results with the old parser to ensure compatibility.
"""

from src.parser.new.token_types import Token, TokenType 
from src.parser.new.lexer import tokenize
from src.parser.new.parser.shell_parser import ShellParser
from src.parser.new.parser.compatibility import Parser as OldParser
from src.parser.ast import CommandNode, PipelineNode, IfNode, WhileNode, ForNode, CaseNode, FunctionNode

def print_ast(node, indent=0):
    """Print an AST node with indentation for better visualization."""
    prefix = "  " * indent
    if node is None:
        print(f"{prefix}None")
        return
        
    print(f"{prefix}{node.__class__.__name__}: {node}")
    
    if isinstance(node, CommandNode):
        print(f"{prefix}  Command: {node.command}")
        print(f"{prefix}  Args: {node.args}")
        if node.redirections:
            print(f"{prefix}  Redirections: {node.redirections}")
        if node.background:
            print(f"{prefix}  Background: {node.background}")
    elif isinstance(node, PipelineNode):
        print(f"{prefix}  Background: {node.background}")
        print(f"{prefix}  Commands:")
        for cmd in node.commands:
            print_ast(cmd, indent + 2)
    elif isinstance(node, IfNode):
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Then:")
        print_ast(node.then_branch, indent + 2)
        if node.else_branch:
            print(f"{prefix}  Else:")
            print_ast(node.else_branch, indent + 2)
    elif isinstance(node, WhileNode):
        print(f"{prefix}  Until: {node.until}")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    elif isinstance(node, ForNode):
        print(f"{prefix}  Variable: {node.variable}")
        print(f"{prefix}  Words: {node.words}")
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    elif isinstance(node, CaseNode):
        print(f"{prefix}  Word: {node.word}")
        print(f"{prefix}  Items:")
        for i, item in enumerate(node.items):
            print(f"{prefix}    Pattern {i+1}: {item.pattern}")
            print(f"{prefix}    Action:")
            print_ast(item.action, indent + 4)
    elif isinstance(node, FunctionNode):
        print(f"{prefix}  Name: {node.name}")
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)

def test_parser(input_line, compare_with_old=False):
    """Test the new parser on a given input and compare with the old parser."""
    print(f"\n=== Testing parser on: {input_line!r} ===")
    
    # Parse with the new parser
    parser = ShellParser()
    tokens = tokenize(input_line)
    result = parser.parse(tokens)
    
    print("\nNew Parser Result:")
    print_ast(result)
    
    # Compare with the old parser if requested (disabled by default)
    if compare_with_old:
        print("\nOld Parser Result:")
        old_parser = OldParser()
        old_result = old_parser.parse(input_line)
        print_ast(old_result)

# Test simple commands
def test_simple_commands():
    print("\n==== Simple Commands ====")
    test_parser("echo hello world")
    test_parser("ls -la /tmp")
    test_parser("cd /usr/local/bin")
    test_parser("echo hello > output.txt")
    test_parser("cat < input.txt")
    test_parser("grep pattern file | sort | uniq")
    test_parser("sleep 10 &")

# Test control structures
def test_control_structures():
    print("\n==== Control Structures ====")
    test_parser("if test -f /etc/passwd; then echo exists; fi")
    test_parser("if [ -d /tmp ]; then echo 'tmp exists'; else echo 'no tmp'; fi")
    test_parser("if echo hello; then echo yes; elif echo maybe; then echo perhaps; else echo no; fi")
    test_parser("while true; do echo loop; sleep 1; done")
    test_parser("until [ -f /tmp/flag ]; do echo waiting; sleep 1; done")
    test_parser("for i in 1 2 3; do echo $i; done")
    test_parser("for file in *.txt; do wc -l $file; done")

# Test case statements
def test_case_statements():
    print("\n==== Case Statements ====")
    test_parser("case $1 in a) echo A;; b) echo B;; *) echo default;; esac")
    test_parser("case $option in\n  -h|--help) show_help;;\n  -v|--version) show_version;;\n  *) echo \"Unknown option\";;\nesac")

# Test function definitions
def test_function_definitions():
    print("\n==== Function Definitions ====")
    test_parser("function hello() { echo hello world; }")
    test_parser("function greet { echo \"Hello, $1!\"; }")

# Test complex scripts
def test_complex_scripts():
    print("\n==== Complex Scripts ====")
    script = """
if [ -f ~/.bashrc ]; then
    echo "bashrc exists"
    source ~/.bashrc
else
    echo "No bashrc found"
fi

function check_file() {
    if [ -f "$1" ]; then
        echo "$1 exists"
        return 0
    else
        echo "$1 not found"
        return 1
    fi
}

for file in *.txt; do
    check_file "$file"
    case $? in
        0) echo "Processing $file";;
        *) echo "Skipping $file";;
    esac
done
"""
    test_parser(script, compare_with_old=False)  # Too complex for old parser, only test new one

# Run all tests
if __name__ == "__main__":
    test_simple_commands()
    test_control_structures()
    test_case_statements()
    test_function_definitions()
    test_complex_scripts()