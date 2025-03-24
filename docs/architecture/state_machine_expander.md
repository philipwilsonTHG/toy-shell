# State Machine Expander Architecture

## Overview
The state machine expander is an optimization implementation for variable expansion in the Python Shell (psh). It replaces the previous regex-based approach with a more efficient character-by-character state machine. This document outlines the architecture and key components of this implementation.

## Module Structure

As of the recent refactoring, the state machine expander implementation has been divided into multiple modules under the `src/parser/state_machine/` directory for improved maintainability:

```
src/parser/state_machine/
├── __init__.py           # Exports main components
├── types.py              # TokenType, Token, and State definitions
├── context.py            # StateContext class
├── tokenizer.py          # Tokenizer implementation
├── pattern_utils.py      # Shell pattern handling utilities
├── variable_modifiers.py # Functions for handling modifiers (${VAR#pattern}, etc.)
├── expander.py           # Main StateMachineExpander class
```

For backward compatibility, `src/parser/state_machine_expander.py` re-exports all components from these modules.

## Key Components

### 1. TokenType (Enum) - `types.py`
Defines different token types that can be identified during tokenization:
- `LITERAL`: Regular text with no special handling
- `VARIABLE`: Variable reference like $VAR
- `BRACE_VARIABLE`: Variable reference with braces like ${VAR}
- `ARITHMETIC`: Arithmetic expression like $((expr))
- `COMMAND`: Command substitution like $(cmd)
- `BACKTICK`: Alternative command substitution like `cmd`
- `SINGLE_QUOTED`: Text inside single quotes (no expansion)
- `DOUBLE_QUOTED`: Text inside double quotes (limited expansion)
- `ESCAPED_CHAR`: Escaped character like \$
- `BRACE_PATTERN`: Brace expansion pattern like {a,b,c}

### 2. Token (Class) - `types.py`
Represents a token with:
- `type`: The token type (from TokenType enum)
- `value`: The token's value (text content)
- `raw`: Original text (useful for preserving original input when needed)

### 3. State (Enum) - `types.py`
Defines the different states for the state machine:
- `NORMAL`: Regular text processing
- `DOLLAR`: Just seen a $ character, determining what follows
- `VARIABLE`: Processing a variable name
- `BRACE_START`: Just seen ${, preparing for brace variable
- `BRACE_VARIABLE`: Inside ${...}, processing variable with modifiers
- `PAREN_START`: Just seen $(, determining if command or arithmetic
- `COMMAND`: Inside $(...), processing command substitution
- `ARITHMETIC_START`: Just seen $((, preparing for arithmetic
- `ARITHMETIC`: Inside $((...)), processing arithmetic expression
- `BACKTICK`: Inside backticks, processing command substitution
- `SINGLE_QUOTE`: Inside single quotes (no expansion occurs)
- `DOUBLE_QUOTE`: Inside double quotes (variables expand, literals preserved)
- `ESCAPE`: Just seen a backslash, next character is literal
- `BRACE_PATTERN_START`: Just seen {, preparing for brace pattern
- `BRACE_PATTERN`: Inside {...}, processing brace expansion pattern

### 4. StateContext (Class) - `context.py`
Manages the state machine context, tracking:
- Current position in the input text
- Current state and state stack for nested constructs
- Token collection and current token start position
- Nesting counters for braces and parentheses
- Debug output control

Key methods:
- `push_state()`: Push a new state onto the stack for nested processing
- `pop_state()`: Pop state when exiting nested constructs
- `add_token()`: Add a completed token to the token list

### 5. Tokenizer (Class) - `tokenizer.py`
Core component that implements the state machine for tokenization:
- Processes text character-by-character in a single pass
- Uses a state handler for each possible state
- Transitions between states based on current character and state
- Handles nested structures using counters and state stack
- Creates appropriate tokens for different shell constructs

### 6. Pattern Utilities - `pattern_utils.py`
Utility functions for shell pattern handling:
- `shell_pattern_to_regex()`: Converts shell wildcards to regex patterns
- `split_brace_pattern()`: Splits brace patterns respecting nesting

### 7. Variable Modifiers - `variable_modifiers.py`
Functions for handling shell variable modifiers:
- `handle_pattern_removal()`: Handles ${VAR#pattern} and ${VAR%pattern}
- `handle_pattern_substitution()`: Handles ${VAR/pattern/replacement}
- `handle_case_modification()`: Handles ${VAR^}, ${VAR^^}, etc.

### 8. StateMachineExpander (Class) - `expander.py`
Expands shell constructs using tokens from the Tokenizer:
- Takes a scope provider function to look up variable values
- Tokenizes input text with the Tokenizer
- Expands each token according to its type
- Provides specialized handling for different expansion types:
  - Variable expansion with modifiers (${VAR:-default}, etc.)
  - Arithmetic evaluation with variable support
  - Command substitution (both $() and backtick styles)
  - Brace pattern expansion ({a,b,c} and {1..5})
- Implements caching for variables and arithmetic expressions
- Provides fast paths for common cases

### 9. StateMachineWordExpander (Adapter Class)
Adapter to make the state machine implementation compatible with the existing interface:
- Conforms to the same API as the original WordExpander
- Maps API calls to the appropriate StateMachineExpander methods
- Ensures backward compatibility with existing code
- Provides cache invalidation mechanism

## Performance Optimizations

1. **Single Pass Processing**: Replaces multiple regex passes with a single character-by-character scan
2. **State-Based Approach**: Handles complex nesting more efficiently with explicit state tracking
3. **Caching**:
   - Variable lookup results cached to avoid redundant lookups
   - Arithmetic expression results cached for repeated expressions
   - Cache invalidation when variables change
4. **Fast Paths**:
   - Early return for strings without expansion markers
   - Special handling for common cases to avoid full tokenization
5. **Reduced String Manipulations**:
   - Less intermediate string creation compared to regex approach
   - Avoids excessive string concatenation

## Testing

The state machine expander is thoroughly tested with unit tests covering:
- Tokenization of various shell constructs
- Variable expansion with and without modifiers
- Arithmetic expression evaluation
- Command substitution
- Handling of quotes and escapes
- Brace pattern expansion
- Nested constructs
- Edge cases and error handling

## Integration

The StateMachineWordExpander adapter allows seamless integration with the existing shell code:
- Can be used as a drop-in replacement for the original WordExpander
- Maintains the same API surface while improving performance
- No changes required to calling code