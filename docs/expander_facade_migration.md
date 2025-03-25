# Expander Facade Migration Guide

The `expander_facade.py` module is now deprecated and will be removed in a future version. 
This guide will help you migrate from using the facade to using the `StateMachineExpander` class directly.

## Why Migrate?

- **Better Performance**: Using the StateMachineExpander directly avoids unnecessary function calls
- **More Control**: Direct access to all expander features and configuration options
- **Better Type Checking**: Better typing information for the expander methods
- **Future-Proof**: The StateMachineExpander is the supported API going forward

## Migration Steps

### Step 1: Update Imports

Replace imports from `expander_facade` with imports from `state_machine_expander`:

```python
# Old imports
from src.parser.expander_facade import expand_variables, expand_all

# New imports
from src.parser.state_machine_expander import StateMachineExpander
```

### Step 2: Create an Expander Instance

Create an instance of the StateMachineExpander with the appropriate scope provider:

```python
# For environment variables (most common case)
expander = StateMachineExpander(os.environ.get, debug_mode=False)

# For custom variable scope (e.g., in tests)
expander = StateMachineExpander(my_scope.get, debug_mode=True)
```

### Step 3: Replace Function Calls

Replace calls to the facade functions with calls to the StateMachineExpander methods:

| Old (Facade)                       | New (StateMachineExpander)                   |
|------------------------------------|----------------------------------------------|
| `expand_variables(text)`           | `expander.expand_variables(text)`            |
| `expand_all(text)`                 | `expander.expand_all_with_brace_expansion(text)` |
| `expand_command_substitution(text)`| `expander.expand_command(text)`              |
| `expand_arithmetic(text)`          | `expander.expand_arithmetic(text)`           |
| `expand_tilde(text)`               | `expander.expand_tilde(text)`                |
| `expand_wildcards(text)`           | `expander.expand_wildcards(text)`            |
| `expand_braces(text)`              | `expander.expand_braces(text)`               |

### Example Migration

Here's a complete example of migrating from the facade to direct StateMachineExpander usage:

#### Before:

```python
import os
from src.parser.expander_facade import expand_variables, expand_all

def process_command(command):
    # Expand variables in command
    command = expand_variables(command)
    
    # Expand all constructs in arguments
    args = [expand_all(arg) for arg in command.split()]
    
    return args
```

#### After:

```python
import os
from src.parser.state_machine_expander import StateMachineExpander

def process_command(command):
    # Create an expander
    expander = StateMachineExpander(os.environ.get)
    
    # Expand variables in command
    command = expander.expand_variables(command)
    
    # Expand all constructs in arguments
    args = [expander.expand_all_with_brace_expansion(arg) for arg in command.split()]
    
    return args
```

## Performance Optimization

For better performance, consider creating a single StateMachineExpander instance and reusing it:

```python
import os
from src.parser.state_machine_expander import StateMachineExpander

# Create a global expander instance
EXPANDER = StateMachineExpander(os.environ.get)

def process_command(command):
    # Use the global expander instance
    command = EXPANDER.expand_variables(command)
    args = [EXPANDER.expand_all_with_brace_expansion(arg) for arg in command.split()]
    return args
```

## Testing

When writing tests, create an expander with a custom scope for better test isolation:

```python
def test_expansion():
    # Create a test scope
    variables = {
        'TEST_VAR': 'test_value',
        'PATH': '/test/bin'
    }
    
    # Create an expander with the test scope
    expander = StateMachineExpander(variables.get)
    
    # Run tests with the isolated expander
    result = expander.expand_variables('$TEST_VAR')
    assert result == 'test_value'
```

## Timeline

- **Current Release**: Deprecated warnings added to facade functions
- **Next Major Release**: The `expander_facade.py` module will be removed

If you have any questions about migrating from the facade, please open an issue on the project repository.