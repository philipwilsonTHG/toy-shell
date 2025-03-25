# Expander Architecture

## Overview

The expander system is responsible for handling all shell expansions, including variable expansion, arithmetic evaluation, command substitution, tilde expansion, and brace expansion. It follows the POSIX shell expansion rules in this order:

1. Brace expansion
2. Tilde expansion
3. Parameter expansion, command substitution, arithmetic expansion
4. Word splitting
5. Pathname expansion

## Components

### StateMachineExpander

The core expander component is the `StateMachineExpander` class, which uses a state machine approach to tokenize and expand shell text. It provides methods for all types of expansions and follows a consistent architectural pattern.

#### Key Methods

- `expand(text)`: Main entry point that expands all shell constructs in text
- `expand_all_with_brace_expansion(text)`: Performs all expansions including brace expansion
- `expand_variables(text)`: Expands only variables in text
- `expand_command(text)`: Expands only command substitutions
- `expand_arithmetic(text)`: Expands only arithmetic expressions
- `expand_tilde(text)`: Expands tilde (~) in paths
- `expand_wildcards(text)`: Expands wildcards using glob

#### Implementation Details

The expander uses a modular approach with specialized methods:

- `_expand_double_quoted()`: Handles double-quoted strings with proper space preservation
- `_expand_nested_variable()`: Handles nested variable expansions like `${${VAR%.*},,}`
- `_expand_mixed_text()`: Handles text with mixed content while preserving spaces
- `_expand_token()`: Expands a single token based on its type
- `_expand_variable()`, `_expand_brace_variable()`, etc.: Handle specific token types

### Expander Facade (Deprecated)

> **Note**: The `expander_facade.py` module is now deprecated and will be removed in a future version. Please use the StateMachineExpander class directly instead. See the [Expander Facade Migration Guide](../expander_facade_migration.md) for details.

The `expander_facade.py` module historically provided a simple interface to the expander system, following the Facade design pattern. It delegates all calls to the core StateMachineExpander implementation.

#### Functions (Deprecated)

- `expand_variables(text)`: Expands variables in text
- `expand_all(text)`: Performs all expansions, including brace expansion
- `expand_command_substitution(text)`: Expands command substitutions
- `expand_tilde(text)`: Expands tilde in paths
- `expand_wildcards(text)`: Expands wildcards
- `expand_arithmetic(text)`: Expands arithmetic expressions
- `expand_braces(text)`: Expands brace patterns

## Design Principles

1. **Single Responsibility**: Each component has a clear responsibility
2. **Proper Delegation**: The facade delegates to the core implementation
3. **Clean API**: All public methods have consistent signatures and documentation
4. **Quote Handling**: Special handling of quoted text with expansions
5. **Space Preservation**: Proper space preservation in expansions
6. **Testable**: Core methods are unit tested independent of the facade

## Usage Examples

### Basic Variable Expansion

```python
import os
from src.parser.state_machine_expander import StateMachineExpander

# Create an expander
expander = StateMachineExpander(os.environ.get)

# Expand a simple variable
result = expander.expand_variables("$HOME")

# Expand a variable with modifiers
result = expander.expand_variables("${PATH:-/usr/bin}")
```

### Command Substitution

```python
import os
from src.parser.state_machine_expander import StateMachineExpander

# Create an expander
expander = StateMachineExpander(os.environ.get)

# Expand a command substitution
result = expander.expand_command("$(echo hello)")
```

### Full Expansion

```python
import os
from src.parser.state_machine_expander import StateMachineExpander

# Create an expander
expander = StateMachineExpander(os.environ.get)

# Perform all expansions
result = expander.expand_all_with_brace_expansion("$USER is using $(hostname)")
```

### Reusing an Expander Instance

```python
import os
from src.parser.state_machine_expander import StateMachineExpander

# Create a global expander instance
EXPANDER = StateMachineExpander(os.environ.get)

def process_command(command):
    # Expand variables
    command = EXPANDER.expand_variables(command)
    
    # Split and expand arguments
    args = command.split()
    expanded_args = [EXPANDER.expand_all_with_brace_expansion(arg) for arg in args]
    
    return expanded_args
```