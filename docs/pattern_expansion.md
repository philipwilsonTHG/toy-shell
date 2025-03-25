# Advanced Pattern Expansion

## Overview

The psh shell now includes enhanced pattern expansion capabilities in the state machine expander. These features support complex string manipulations, file path operations, and URL pattern handling, making the shell more powerful for text processing tasks.

## URL Parsing and Pattern Handling

### URL Component Extraction

The shell can parse and extract URL components using pattern expansion:

```bash
# Extract protocol from URL
url="https://example.com/path/to/file.html?param=value"
echo ${url%%://*}  # Output: https

# Remove protocol from URL
echo ${url#*://}   # Output: example.com/path/to/file.html?param=value

# Extract domain from URL
echo ${url#*://}   # Get URL without protocol first
echo ${url#*://}%%/*}  # Extract domain: example.com

# Extract path from URL
echo ${url#*://*/}  # Output: path/to/file.html?param=value

# Extract query string 
echo ${url#*\?}    # Output: param=value

# Remove query string
echo ${url%\?*}    # Output: https://example.com/path/to/file.html
```

### URL Parsing Implementation

The implementation uses both Python's `urlparse` library for standard URLs and a custom fallback parser for handling edge cases. The main components are:

1. `parse_url_components()`: Comprehensive URL parser that handles:
   - Protocol/scheme extraction
   - Domain/host parsing
   - Path component handling
   - Query string parsing
   - Fragment identification
   - Authentication components (username/password)
   - Port number extraction

2. `handle_url_pattern()`: Special handler for common URL pattern operations:
   - Protocol removal/extraction
   - Domain isolation
   - Path component extraction
   - Query parameter handling

## File Path Operations

### Path Component Extraction

The shell now properly handles multiple file extensions and complex path operations:

```bash
# File extension operations
filename="document.tar.gz"
echo ${filename%.*}     # Remove last extension: document.tar
echo ${filename%%.*}    # Remove all extensions: document

# Path component operations
path="/usr/local/bin/example"
echo ${path##*/}        # Extract filename: example
echo ${path%/*}         # Remove last component: /usr/local/bin
echo ${path%%/*}        # Remove all components: (empty string)
```

### Multiple Extension Support

The implementation includes specialized handling for multiple extensions with the `handle_multiple_extensions()` function:

- `${filename%.*}`: Removes just the last extension
- `${filename%%.*}`: Removes all extensions (starting from the first dot)

This allows proper manipulation of files with compound extensions like `.tar.gz`, `.min.js.map`, etc.

## Pattern Substitution Enhancements

### Improved Escape Handling

The shell now properly handles escaped delimiters in substitution patterns:

```bash
# Replace forward slashes with colons
path="a/b/c"
echo ${path//\\//:}     # Output: a:b:c

# Double backslashes in paths
winpath="C:\Users\name"
echo ${winpath//\\/\\\\} # Output: C:\\Users\\name
```

### Pattern Substitution Implementation

The implementation includes:

1. Enhanced escape sequence processing for complex patterns
2. Special case handling for common shell idioms
3. Proper handling of backslash-escaped delimiters
4. URL and file path awareness in substitution operations

## Case Modification

The shell supports case conversion operations:

```bash
text="Hello World"
echo ${text,}     # Convert first character to lowercase: hello World
echo ${text,,}    # Convert all characters to lowercase: hello world
echo ${text^}     # Convert first character to uppercase: Hello World
echo ${text^^}    # Convert all characters to uppercase: HELLO WORLD
```

## Implementation Architecture

The pattern expansion implementation is built around several key components:

1. **Pattern Utilities**: In `pattern_utils.py`
   - `shell_pattern_to_regex()`: Converts shell wildcard patterns to regex
   - `parse_url_components()`: URL parser with comprehensive component extraction
   - `handle_multiple_extensions()`: Special handling for file extensions 
   - `handle_url_pattern()`: Context-aware URL pattern operations

2. **Variable Modifiers**: In `variable_modifiers.py`
   - `handle_pattern_removal()`: Implements prefix/suffix removal operations
   - `handle_pattern_substitution()`: Implements substitution with proper escaping
   - `handle_case_modification()`: Implements case conversion operations

3. **State Machine Integration**: 
   - Context-aware handling of different pattern types
   - Special case detection and optimization for common operations
   - Proper precedence and nesting support

## Future Enhancements

The implementation roadmap includes:

1. **Template Substitution**: Enhanced support for format string templates
2. **Version String Manipulation**: Better handling of semantic version components
3. **Date Component Extraction**: Specialized handling for date/time strings 
4. **Key-Value Pair Processing**: Better support for configuration-style strings
5. **Deeply Nested Operations**: Support for complex multi-step operations

## Implementation Principles

The pattern expansion features follow these design principles:

1. **Pattern-First Approach**: Detect and optimize based on pattern type
2. **Progressive Enhancement**: Add special cases for common operations
3. **Fallback Chain**: Use specialized handlers first, then fall back to general implementation
4. **Context Awareness**: Use different strategies based on pattern context (URL, file path, etc.)
5. **Standard Library Integration**: Use Python's standard library where appropriate

## Usage Guidelines

For best results with pattern expansion:

1. Use appropriate modifiers for the task:
   - `#` and `##` to remove from the beginning (shortest/longest match)
   - `%` and `%%` to remove from the end (shortest/longest match)
   - `/` for single substitution, `//` for global substitution
   - `,` and `,,` for lowercase conversion, `^` and `^^` for uppercase

2. Use appropriate patterns:
   - `*://` to match URL protocols
   - `*/` to match directory components
   - `.*` to match file extensions
   - `*\?` to match URL query parameters

3. Combine operations for complex tasks:
   - Extract domain: `${url#*://}%%/*}`
   - Get path without filename: `${path%/*}`
   - Get filename without extension: `${path##*/}%.*}`