# State Machine Expander Integration

## Overview

This document describes the integration of the state machine-based expander into the shell's main code path. The state machine expander provides a more efficient implementation of variable expansion compared to the previous regex-based approach.

## Changes Made

1. **Updated AST Executor**: 
   - Modified `ASTExecutor` to use `StateMachineWordExpander` instead of `WordExpander`
   - The expander is created with the same scope provider function to maintain compatibility

2. **Updated Shell Class**:
   - Added an instance of `StateMachineWordExpander` to the `Shell` class for direct use
   - Updated the special variable expansion for `$?` to use the state machine expander

3. **Fixed Edge Cases**:
   - Enhanced the adapter to handle special cases involving nested quotes
   - Ensured compatibility with existing test cases

## Benefits

1. **Performance Improvements**:
   - The state machine implementation processes text in a single pass
   - Avoids multiple regex passes and excessive string manipulation
   - Uses caching for variable lookups and arithmetic expressions

2. **Better Handling of Complex Constructs**:
   - More accurate handling of nested constructs
   - Explicit handling of different states for different shell constructs
   - Better error recovery

3. **Maintainability**:
   - Clearer separation of concerns
   - More structured approach with states and transitions
   - Easier to extend with new features

## Compatibility

The integration uses the adapter pattern through `StateMachineWordExpander` to ensure backward compatibility with existing code. The adapter implements the same API as the original `WordExpander`, allowing it to be used as a drop-in replacement.

## Future Enhancements

1. **Performance Monitoring**:
   - Add metrics to track performance improvements
   - Monitor memory usage for long-running shells

2. **Extended Features**:
   - Add support for more complex parameter expansions
   - Optimize command substitution further
   - Improve error reporting for invalid expansions

3. **Full Migration**:
   - Eventually fully replace the old expander code
   - Remove legacy methods once all dependencies have been updated