# Parameter Expansion Test Coverage

This document outlines the test coverage for parameter expansion features in the Python shell (psh) implementation.

## Current Test Coverage

The current parameter expansion implementation passes all original tests in `test_state_machine_expander.py`, which covers the following features:

- Basic variable expansion (`$VAR` and `${VAR}`)
- Default value with alternate value modifiers (`${VAR:-default}`, `${VAR:+alternate}`)
- Pattern removal - both prefix and suffix, shortest and longest match (`${VAR#pattern}`, `${VAR##pattern}`, `${VAR%pattern}`, `${VAR%%pattern}`)
- Case modification - both uppercase and lowercase, first character and all characters (`${VAR^}`, `${VAR^^}`, `${VAR,}`, `${VAR,,}`)
- String length calculation (`${#VAR}`)
- Pattern substitution - both first occurrence and all occurrences (`${VAR/pattern/replacement}`, `${VAR//pattern/replacement}`)
- Nested parameter expansions through specific test cases

## Additional Test Coverage

Additional test files have been created to extend coverage for more complex parameter expansion scenarios:

### test_expansion_modifiers.py

This file tests edge cases and practical usage patterns for parameter expansion modifiers:

- Pattern removal with multiple matches in paths
- Pattern removal with non-matching patterns
- Pattern removal with different wildcard combinations
- Complex pattern removal scenarios for URLs and paths
- Pattern substitution edge cases (empty patterns, empty replacements)
- Case modification edge cases (empty strings, special characters)
- String length edge cases
- Complex nested modifier combinations
- Whitespace handling
- Multiple extensions in filenames
- Pattern substitution with regex-like behaviors

### test_advanced_expansion.py

This file tests real-world usage patterns for parameter expansion that emulate common shell scripts:

- File path manipulations (extracting directories, filenames, extensions)
- URL manipulations (extracting protocols, domains, paths)
- Version string manipulations (extracting major/minor/patch versions)
- Database URL parsing
- Git URL manipulations
- CSV data manipulations
- Key-value data manipulations
- Hostname and domain manipulations
- Date and timestamp manipulations
- Complex nested operations
- Template substitution patterns
- Conditional parameter expansion patterns

### test_expansion_edge_cases.py

This file tests edge cases and potential failure modes:

- Empty and null values
- Indirect variable references
- Unicode and emoji handling
- Special character handling
- Pattern removal with special characters
- Nesting at variable boundaries
- Multiple extensions in filenames
- Path normalization (with . and .. segments)
- Long string handling
- Complex URL parsing
- Escape sequence handling
- Deeply nested expansions
- Parameter expansion at string boundaries
- Escaped characters in modifiers

## Areas for Improvement

Based on test failures, these are areas where parameter expansion support could be enhanced:

1. **Generic Pattern Matching**: 
   - Implement more generic pattern matching for removal operators instead of special-casing specific patterns
   - Better support for wildcards (* and ?) in patterns
   - Proper handling of character classes in patterns

2. **Nested Parameter Expansion**: 
   - More robust support for nested parameter expansions like `${${VAR%.*},,}`
   - Support for multi-level indirection

3. **Special Character Handling**:
   - Better handling of escape sequences in patterns
   - Support for character classes and special pattern characters

4. **Complex Pattern Operations**:
   - Better support for complex URL/path manipulations
   - Support for data format parsing (CSV, key-value pairs)

5. **Unicode and Internationalization**:
   - Ensure proper handling of Unicode characters in all operations
   - Proper case conversion for international characters

## Implementation Strategy

The implementation strategy could follow these steps:

1. Refactor the existing pattern matching code to use more generic approaches instead of special cases
2. Improve the regular expression conversion in `_shell_pattern_to_regex` to handle more complex patterns
3. Enhance the nested parameter expansion support to handle arbitrary nesting levels
4. Add better handling for special characters and escape sequences in patterns
5. Implement proper handling for character classes in pattern matching
6. Add comprehensive error handling for edge cases

## Test-Driven Development Approach

The existing test cases can serve as acceptance criteria for the improved implementation. The approach would be:

1. Fix one test category at a time (e.g., pattern removal, then pattern substitution)
2. For each category, implement the generic solution
3. Run the tests to verify the implementation
4. Refactor to improve code quality
5. Move to the next category

This approach ensures that each enhancement builds on a stable foundation and maintains compatibility with existing features.