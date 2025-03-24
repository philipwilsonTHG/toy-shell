# Advanced Pattern Expansion Implementation TODO

This document outlines advanced shell pattern expansion features that still need to be implemented in the `StateMachineExpander` class. These advanced features currently fail in test cases but don't impact the core shell functionality.

## 1. URL Parsing and Manipulation

### 1.1 Complex URL Query String Extraction
- Example: `${COMPLEX_URL#*\?}` to extract query parameters
- Status: Improved but not fully implemented - basic utilities added for URL parsing
- Files: `test_expansion_edge_cases.py::test_complex_url_parsing`
- Implementation Progress: Added `parse_url_components` function with URL parsing utilities

### 1.2 Nested URL Component Extraction
- Example: `${${API_ENDPOINT#*://}%%/*}` to extract domain without protocol
- Status: Improved but still needs support for multi-step variable tracking
- Files: `test_advanced_expansion.py::test_url_manipulations`
- Implementation Progress: Enhanced pattern matching but needs better variable state tracking

## 2. Advanced Pattern Modifiers and Escaping

### 2.1 Escaped Delimiters in Substitution Patterns
- Example: `${VAR//\\{pattern\\}/${REPLACEMENT}}`
- Status: Improved but needs more work - basic escape handling added
- Files: `test_expansion_edge_cases.py::test_modifier_with_escaped_delimiters`
- Implementation Progress: Added initial escape character handling in pattern_substitution

### 2.2 Special Modifiers Escape Handling
- Example: Complex escaped patterns like `${PATH//\\/\\\\}`
- Status: Partially implemented with special case handling
- Files: `test_expansion_edge_cases.py::test_special_modifiers_escape_handling`
- Implementation Progress: Added specific handling for backslash escaping in substitution patterns

## 3. Complex File Path Operations

### 3.1 Multiple Extensions Handling
- Example: `${FILENAME%%.*}` vs `${FILENAME%.*}` for files like "document.tar.gz"
- Status: Partially implemented with dedicated function
- Files: `test_expansion_edge_cases.py::test_multiple_extensions`
- Implementation Progress: Added `handle_multiple_extensions` function for better extension handling

### 3.2 Git URL Manipulations
- Example: Extracting components from git URLs
- Status: Complex pattern matching and extraction not working
- Files: `test_advanced_expansion.py::test_git_url_manipulations`

## 4. Template Substitution Patterns

### 4.1 Multiple Placeholder Replacements
- Example: Replacing `{{NAME}}` and `{{SERVICE}}` in templates
- Status: Multi-step substitution with special characters not properly handled
- Files: `test_advanced_expansion.py::test_template_substitution_patterns`

## 5. Version String and Date Manipulations

### 5.1 Version Component Extraction
- Example: Extracting major.minor from complex semver
- Status: Multi-step string manipulation not reliable
- Files: `test_advanced_expansion.py::test_version_string_manipulations`

### 5.2 Date Component Extraction
- Example: Extracting year, month, day from date strings
- Status: Pattern removal for date components needs improvement
- Files: `test_advanced_expansion.py::test_date_manipulations`

## 6. Key-Value and CSV Manipulations

### 6.1 Key-Value Pair Extraction
- Example: Parsing "key=value" strings from configuration
- Status: Complex pattern extraction not working correctly
- Files: `test_advanced_expansion.py::test_key_value_manipulations`

### 6.2 CSV Data Field Extraction
- Example: Extracting specific fields from CSV-like data
- Status: Delimiter-based extraction needs improvement
- Files: `test_advanced_expansion.py::test_csv_data_manipulations`

## 7. Deeply Nested Operations

### 7.1 Complex Nested Pattern Operations
- Example: `${${${VAR%suffix}#prefix}^^}`
- Status: Multi-level nesting with different operations not fully supported
- Files: `test_advanced_expansion.py::test_complex_nested_operations`

## Implementation Recommendations

1. **Improve Pattern Escaping**: Create a more robust mechanism for handling escaped characters in patterns
2. **Enhance Multiple Operation Support**: Implement better support for applying multiple operations in sequence
3. **Add Memory for Variable Expansion**: Create a mechanism to properly track and resolve variable values between expansion steps
4. **Implement Better URL Parsing**: Add special handling for URL components using proper URL parsing
5. **Improve Character Class Handling**: Enhance support for character classes in patterns
6. **Add Format String Templates**: Support format string templates for more complex text manipulation

## Priority Order

1. URL parsing and manipulation (1.1, 1.2)
2. Escaped delimiters handling (2.1, 2.2)
3. File path operations (3.1, 3.2)
4. Version string manipulation (5.1)
5. Template substitution (4.1)
6. Date handling (5.2)
7. Key-value and CSV operations (6.1, 6.2)
8. Deeply nested operations (7.1)