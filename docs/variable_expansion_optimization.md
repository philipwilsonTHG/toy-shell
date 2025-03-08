# Variable Expansion Optimization Strategy

This document outlines the strategy for optimizing variable expansion in the Python Shell.

## Current Implementation Analysis

The current variable expansion implementation has several performance bottlenecks:

1. **Multiple Regex Passes**: Each expansion type requires separate regex passes over the text
2. **Recursive Processing**: Brace expansion uses recursion which can be expensive for deeply nested patterns
3. **String Manipulations**: Heavy use of string operations and regex replacements
4. **Command Substitution**: Creates subprocess for each command substitution, which is expensive

## Optimization Strategy

### 1. State Machine Approach
- Replace regex-based parsing with a character-by-character state machine
- Define explicit states for different expansion contexts (normal text, variable, quotes, etc.)
- Process input in a single pass with transition rules between states
- Handle nesting and complex patterns more efficiently
- Reduce intermediate string allocations

### 2. Tokenize-Based Approach
- As an intermediate step before full state machine implementation
- Replace multiple regex passes with a single tokenization phase
- Process tokens in a stream rather than multiple string transformations
- Precompile regex patterns for better performance

### 3. Implement Caching
- Cache recent variable lookups to avoid redundant lookups
- Cache arithmetic expression evaluations
- Use Python's `@lru_cache` for efficient caching of method results
- Add cache invalidation mechanism when variables change

### 4. Convert Recursion to Iteration
- Replace recursive approaches in brace expansion with stack-based iteration
- Use helper functions for clearer code organization
- Avoid stack overflow for deeply nested patterns

### 5. Lazy Expansion
- Skip expansion for inputs without expansion markers
- Only expand variables when actually needed
- Check for expansion markers before performing expensive operations
- Early return for common cases
- Defer command substitution until absolutely necessary

### 6. Command Substitution Optimization
- Add shortcut checks before running command substitutions
- Add memoization for repeated command patterns
- Batch related command substitutions where possible

### 7. Other Optimizations
- Pre-compile regex patterns at class level
- Use fast paths for common cases
- Split complex functions into smaller, focused functions
- Add debug print helper for consistent debugging output

## Implementation Plan

1. First Phase: Immediate Optimizations
   - Update `WordExpander` class with caching and tokenization
   - Replace recursive brace expansion with iterative approach
   - Optimize expand_all function with lazy evaluation
   - Add proper cache invalidation when variables change

2. Second Phase: State Machine Implementation
   - Create a `TokenType` enum for different expansion states
   - Implement a `Tokenizer` class with state transitions
   - Design state transition logic for different expansion contexts
   - Replace regex-based expansion with state machine processing
   - Update `WordExpander` to use the new state machine approach

3. Testing and Benchmarking
   - Run comprehensive tests to verify correctness
   - Benchmark to confirm performance improvements
   - Compare performance with original implementation
   - Document performance gains

## State Machine Design

The state machine for variable expansion will have the following states:

1. `LITERAL` - Normal text, no special processing
2. `DOLLAR` - Just seen a `$`, looking for what comes next
3. `VARIABLE` - Processing a variable name
4. `BRACE_VARIABLE` - Processing a ${variable} construct
5. `ARITHMETIC` - Processing a $((expression))
6. `COMMAND` - Processing a $(command)
7. `BACKTICK` - Processing a `command`
8. `SINGLE_QUOTE` - Inside single quotes (no expansion)
9. `DOUBLE_QUOTE` - Inside double quotes (limited expansion)
10. `ESCAPE` - Just seen a backslash, next character is literal

Transitions between states will be driven by the current character and current state, with special handling for nested constructs.