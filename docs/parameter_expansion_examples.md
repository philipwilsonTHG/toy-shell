# Parameter Expansion Examples

This document provides examples of parameter expansion in the Python Shell (psh), demonstrating how to use various modifiers for string manipulation.

## Basic Parameter Expansion

```bash
# Simple variable reference
echo $HOME
echo ${USER}

# Default values
echo ${UNDEFINED:-default value}  # Use default if variable is unset or empty
echo ${USER:=fallback}            # Assign default if variable is unset or empty
echo ${EMPTY:?error message}      # Display error if variable is unset or empty
echo ${USER:+alternate value}     # Use alternate value if variable is set and non-empty
```

## String Length

```bash
# Get string length
echo ${#HOME}                     # Length of HOME variable
```

## Pattern Removal

### Prefix Removal

```bash
# Remove shortest matching prefix
filename="path/to/document.txt"
echo ${filename#*/}               # Removes "path/" -> "to/document.txt"

# Remove longest matching prefix
echo ${filename##*/}              # Removes "path/to/" -> "document.txt"
```

### Suffix Removal

```bash
# Remove shortest matching suffix
filename="archive.tar.gz"
echo ${filename%.*}               # Removes ".gz" -> "archive.tar"

# Remove longest matching suffix
echo ${filename%%.*}              # Removes ".tar.gz" -> "archive"
```

## Pattern Substitution

```bash
# Replace first occurrence
text="hello world hello"
echo ${text/hello/hi}             # Replace first "hello" -> "hi world hello"

# Replace all occurrences
echo ${text//hello/hi}            # Replace all "hello" -> "hi world hi"

# Replace at the beginning
echo ${text/#hello/hi}            # Replace if at beginning -> "hi world hello"

# Replace at the end
echo ${text/%hello/goodbye}       # Replace if at end -> "hello world goodbye"
```

## Case Modification

```bash
# Uppercase first character
name="john"
echo ${name^}                     # First char uppercase -> "John"

# Uppercase all characters
echo ${name^^}                    # All chars uppercase -> "JOHN"

# Lowercase first character
NAME="JOHN"
echo ${NAME,}                     # First char lowercase -> "jOHN"

# Lowercase all characters
echo ${NAME,,}                    # All chars lowercase -> "john"
```

## Combining Modifiers

Parameter expansions can be combined for more complex operations. Note that these require nesting expansions.

```bash
# Extract filename and convert to uppercase
path="/home/user/document.txt"
filename=${path##*/}              # Extract filename -> "document.txt"
echo ${filename^^}                # Convert to uppercase -> "DOCUMENT.TXT"

# Remove extension and convert to lowercase
echo ${${filename%.*},,}          # Remove .txt and lowercase -> "document"
```

## Real-World Examples

### File Path Operations

```bash
path="/usr/local/share/doc/example.tar.gz"

# Extract directory
echo ${path%/*}                   # -> "/usr/local/share/doc"

# Extract filename
echo ${path##*/}                  # -> "example.tar.gz"

# Extract file extension
echo ${path##*.}                  # -> "gz"

# Remove extension
echo ${path%.*}                   # -> "/usr/local/share/doc/example.tar"

# Replace extension
echo ${path%.*}.bak               # -> "/usr/local/share/doc/example.tar.bak"
```

### URL Parsing

```bash
url="https://example.com/path/to/file.html?param=value"

# Extract protocol
echo ${url%%://*}                 # -> "https"

# Remove protocol
echo ${url#*://}                  # -> "example.com/path/to/file.html?param=value"

# Extract domain
domain=${url#*://}
echo ${domain%%/*}                # -> "example.com"

# Extract path
path=${url#*://*/}
echo ${path%%\?*}                 # -> "file.html"

# Extract query string
echo ${url#*\?}                   # -> "param=value"
```

### Version String Parsing

```bash
version="1.2.3-beta.4"

# Extract major version
echo ${version%%.*}               # -> "1"

# Extract minor version
minor=${version#*.}
echo ${minor%%.*}                 # -> "2"

# Extract patch version
echo ${version##*.}               # -> "4"

# Remove pre-release tag
echo ${version%%-*}               # -> "1.2.3"
```

### Template Replacement

```bash
template="Hello {{NAME}}, welcome to {{SERVICE}}!"
name="User"
service="Shell"

# Replace placeholders
temp=${template//\{\{NAME\}\}/$name}
echo ${temp//\{\{SERVICE\}\}/$service}  # -> "Hello User, welcome to Shell!"
```

### CSV Data Parsing

```bash
csv="field1,field2,field3,field4"

# Get first field
echo ${csv%%,*}                   # -> "field1"

# Get last field
echo ${csv##*,}                   # -> "field4"

# Change delimiter
echo ${csv//,/;}                  # -> "field1;field2;field3;field4"
```

## Notes and Limitations

- Not all shell parameter expansion features may be implemented
- Nested expansions like `${${var}...}` depend on implementation support
- The behavior of special characters in patterns may vary
- Complex substitutions may require multiple steps
- Some expansions may be sensitive to whitespace

Refer to the shell documentation for details about implementation-specific features and behaviors.