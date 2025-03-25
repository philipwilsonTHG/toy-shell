# Expander Refactoring Plan

## Current Issues

The current implementation of the expander system has several architectural issues:

1. **Logic in Facade**: The `expander_facade.py` contains significant business logic, violating the facade pattern
2. **Special Case Handling**: Special cases are handled in the facade rather than the core implementation
3. **Mixed Responsibilities**: The facade both adapts interfaces and implements core functionality
4. **Maintenance Challenges**: Adding special case handling to the facade makes maintenance difficult

## Refactoring Goals

1. Move all expansion logic to the core `StateMachineExpander` class
2. Make the facade a thin wrapper that delegates to the core implementation
3. Improve maintainability by centralizing expansion logic
4. Follow the Single Responsibility Principle throughout the system

## Implementation Plan

### Phase 1: Enhance Core Implementation

1. Add new methods to `StateMachineExpander` to handle special cases:
   - `_expand_double_quoted()`: Handle double-quoted strings with proper space preservation
   - `_expand_nested_variable()`: Handle nested variable expansions
   - `_expand_mixed_text()`: Handle text with mixed content, preserving spaces

2. Refactor the `expand()` method to use these new methods:
   ```python
   def expand(self, text: str) -> str:
       """
       Expand all shell constructs in the input text
       
       Args:
           text: The input text to expand
           
       Returns:
           The expanded text
       """
       # Debug logging if enabled
       if self.debug_mode:
           print(f"[DEBUG] Expanding: '{text}'", file=sys.stderr)
       
       # Fast path for empty or simple strings
       if not text or not any(c in text for c in ('$', '{', '`', '\\', '\'', '"')):
           return text
           
       # Special handling for quoted strings
       if text.startswith('"') and text.endswith('"') and len(text) >= 2:
           # For double-quoted strings, expand the content with proper space handling
           return self._expand_double_quoted(text)
       elif text.startswith("'") and text.endswith("'") and len(text) >= 2:
           # For single-quoted strings, return content without expansion
           return text[1:-1]
           
       # Handle nested variable expansion like ${${VAR%.*},,}
       if text.startswith("${") and "${" in text[2:] and text.endswith("}"):
           return self._expand_nested_variable(text)
       
       # For mixed text, tokenize and expand using the proper tokenizer
       if ' ' in text and not text.startswith(('${', '$', '\'')):
           return self._expand_mixed_text(text)
       
       # For unquoted text
       return self.expand_unquoted(text)
   ```

3. Add specialized handling methods:
   ```python
   def _expand_double_quoted(self, text: str) -> str:
       """
       Expand the content of a double-quoted string preserving spaces
       
       Args:
           text: Double-quoted string to expand
           
       Returns:
           Expanded content with spaces preserved
       """
       # Extract content without quotes
       content = text[1:-1]
       
       # Tokenize the content
       tokens = self.tokenizer.tokenize(content)
       
       # Expand each token, preserving spaces
       expanded_parts = []
       for token in tokens:
           if token.type == TokenType.LITERAL:
               # Preserve literal text exactly
               expanded_parts.append(token.value)
           else:
               # Expand other tokens
               expanded = self._expand_token(token)
               expanded_parts.append(expanded)
       
       # Join the parts preserving original spacing
       return ''.join(expanded_parts)
   ```

4. Add additional convenience methods to handle the specific expansion types that the facade currently exposes:
   - `expand_variables(text: str) -> str`
   - `expand_command(text: str) -> str`
   - `expand_tilde(text: str) -> str`
   - `expand_wildcards(text: str) -> List[str]`
   - `expand_arithmetic(text: str) -> str`

### Phase 2: Simplify the Facade

1. Simplify the facade to only delegate to the core implementation:
   ```python
   def expand_variables(text: str) -> str:
       """
       Expand environment variables in text
       
       Args:
           text: Text containing variables to expand
           
       Returns:
           The text with variables expanded
       """
       return _env_expander.expand_variables(text)

   def expand_all(text: str) -> str:
       """
       Perform all expansions on text (variables, arithmetic, command substitution)
       
       Args:
           text: Text to expand
           
       Returns:
           The fully expanded text
       """
       # Simply delegate to the state machine expander
       return _env_expander.expand(text)
   ```

2. Remove any business logic from the facade
3. Keep only the interface adaptation functions (parameter transformation, etc.)

### Phase 3: Testing and Validation

1. Add unit tests for the new methods in `StateMachineExpander`
2. Ensure existing tests continue to pass
3. Add regression tests for the specific cases that were previously handled in the facade

### Phase 4: Documentation and Cleanup

1. Update documentation to reflect the new architecture
2. Add inline comments explaining any complex logic in the core implementation
3. Remove any redundant or deprecated code

## Future Considerations

1. Consider separating the different expansion types into specialized classes for better organization
2. Explore a more flexible token-based expansion system for handling complex nested expansions
3. Develop a more systematic approach to handling quoted text with expansions

## Benefits of This Approach

1. **Cleaner Architecture**: Better separation of concerns between components
2. **Improved Maintainability**: Expansion logic centralized in appropriate classes
3. **Better Testability**: Core logic more easily testable in isolation
4. **Easier Extension**: New expansion types can be added to the core without modifying the facade
5. **Reduced Duplication**: Special case handling in one place rather than scattered