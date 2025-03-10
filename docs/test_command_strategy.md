# Strategy for Implementing POSIX-Compatible Shell Tests in psh

## Implementation Location
Based on the codebase structure, implement the `test` and `[` builtins in:
- Create a new file: `/src/builtins/test.py`
- Register both commands in `/src/builtins/__init__.py`

## Core POSIX Test Operations

### File Tests
- `-e file`: File exists
- `-f file`: Regular file exists
- `-d file`: Directory exists
- `-r/-w/-x file`: Read/write/execute permissions
- `-s file`: Non-empty file
- `-L file`: Symbolic link

### String Tests
- `-z string`: Zero length
- `-n string`: Non-zero length
- `s1 = s2`: String equality
- `s1 != s2`: String inequality

### Integer Comparisons
- `-eq/-ne/-gt/-ge/-lt/-le`: Equality, greater/less than

### Logical Operators
- `!`: Negation
- `-a`: Logical AND
- `-o`: Logical OR
- `( )`: Grouping

## Implementation Approach

```python
def test_command(*args) -> int:
    """POSIX test command implementation."""
    # Handle [ specifically - check for closing ]
    called_as_bracket = False
    args_list = list(args)
    
    if args and args[0] == '[':
        called_as_bracket = True
        if args_list[-1] != ']':
            print("[: missing ']'", file=sys.stderr)
            return 2
        args_list = args_list[1:-1]  # Remove [ and ]
    
    # No arguments case
    if not args_list:
        return 1  # False when no arguments
    
    # Parse and evaluate the expression
    try:
        result = _evaluate_expression(args_list)
        return 0 if result else 1
    except ValueError as e:
        print(f"test: {str(e)}", file=sys.stderr)
        return 2
```

## Integration with Shell Execution
1. Register both names in builtins dictionary:
   ```python
   "test": test_command,
   "[": test_command
   ```

2. Ensure proper exit code handling:
   - 0 for true
   - 1 for false
   - 2 for errors

3. Add comprehensive test suite in `/tests/test_builtins/test_test.py`

## Special Considerations
- Handle quoting and variable expansion correctly
- Implement short-circuit evaluation for logical operators
- Ensure correct precedence of operators
- Handle edge cases like empty arguments
- Support proper error messages for incorrect syntax

## Full Implementation Details

### Expression Evaluation 
Implement a recursive descent parser for test expressions that handles:

```python
def _evaluate_expression(args: List[str]) -> bool:
    """Evaluate a test expression with proper precedence."""
    if not args:
        return False
        
    # Handle OR expressions first (lowest precedence)
    if '-o' in args:
        index = args.index('-o')
        left = _evaluate_expression(args[:index])
        right = _evaluate_expression(args[index+1:])
        return left or right
        
    # Handle AND expressions next
    if '-a' in args:
        index = args.index('-a')
        left = _evaluate_expression(args[:index])
        right = _evaluate_expression(args[index+1:])
        return left and right
    
    # Handle negation
    if args[0] == '!':
        return not _evaluate_expression(args[1:])
    
    # Handle parentheses for grouping
    if args[0] == '(' and args[-1] == ')':
        return _evaluate_expression(args[1:-1])
    
    # Handle binary operators
    if len(args) == 3:
        left, op, right = args
        
        # String comparison
        if op == '=':
            return left == right
        elif op == '!=':
            return left != right
            
        # Integer comparison
        if op in ['-eq', '-ne', '-gt', '-ge', '-lt', '-le']:
            try:
                left_val = int(left)
                right_val = int(right)
            except ValueError:
                raise ValueError(f"integer expression expected: {left} or {right}")
                
            if op == '-eq': return left_val == right_val
            if op == '-ne': return left_val != right_val
            if op == '-gt': return left_val > right_val
            if op == '-ge': return left_val >= right_val
            if op == '-lt': return left_val < right_val
            if op == '-le': return left_val <= right_val
    
    # Handle unary operators
    if len(args) == 2:
        op, operand = args
        
        # String tests
        if op == '-z': return len(operand) == 0
        if op == '-n': return len(operand) > 0
        
        # File tests
        if op == '-e': return os.path.exists(operand)
        if op == '-f': return os.path.isfile(operand)
        if op == '-d': return os.path.isdir(operand)
        if op == '-r': return os.access(operand, os.R_OK)
        if op == '-w': return os.access(operand, os.W_OK)
        if op == '-x': return os.access(operand, os.X_OK)
        if op == '-s': return os.path.exists(operand) and os.path.getsize(operand) > 0
        if op == '-L': return os.path.islink(operand)
        
    # Single argument (non-empty string test)
    if len(args) == 1:
        return bool(args[0])
        
    raise ValueError(f"invalid test expression: {' '.join(args)}")
```

### Error Handling
- Handle all POSIX-specified error conditions
- Provide appropriate error messages
- Ensure correct exit codes

### Test Cases
- Basic operators: Test each operator individually
- Complex expressions: Test expressions with multiple operators
- Edge cases: Empty strings, non-existent files, etc.
- Error cases: Malformed expressions, type errors