# Brace Expansion Implementation Strategy

## Overview

This document outlines the strategy for implementing POSIX-compliant brace expansion in the Python Shell (psh). Brace expansion is a mechanism to generate arbitrary strings that follow patterns like `{a,b,c}` or ranges like `{1..5}`.

## Implementation Plan

1. **Add a new `expand_braces()` function in `src/parser/expander.py`**
   - Handle basic comma-separated patterns: `{a,b,c}` → `a b c`
   - Support numeric and alphabetic ranges: `{1..5}` → `1 2 3 4 5`, `{a..e}` → `a b c d e`
   - Process nested patterns: `a{b,c{d,e}}` → `ab acd ace`
   - Handle prefix/suffix content: `prefix{a,b}suffix` → `prefixasuffix prefixbsuffix`

2. **Update the `expand_all()` function**
   - Add brace expansion as the first step in the expansion process
   - Follow POSIX expansion order: brace expansion → tilde expansion → parameter expansion → command substitution → arithmetic expansion → word splitting → pathname expansion

3. **Implement using recursive regex pattern matching**
   - Use similar approach to the existing command substitution and arithmetic expansion implementations
   - Handle nested braces by recursively processing the inner-most expressions first

4. **Handle quoting rules properly**
   - No expansion inside single quotes: `'{a,b}'` remains literal `{a,b}`
   - Perform expansion inside double quotes: `"{a,b}"` becomes `a b`
   - Respect escape characters: `\{a,b}` remains literal `{a,b}`

5. **Add comprehensive tests**
   - Basic patterns: `{a,b,c}`
   - Numeric ranges: `{1..10}`, `{10..1}`
   - Alphabetic ranges: `{a..z}`, `{Z..A}`
   - Nested patterns: `{a,b{c,d}}`
   - Prefix/suffix: `pre{a,b}post`
   - Quoting tests: `'{a,b}'`, `"{a,b}"`, `\{a,b}`
   - Edge cases: empty elements, single element, no commas

## Example Pseudo-code

```python
def expand_braces(text: str) -> list[str]:
    """Expand brace patterns in text."""
    # If no braces or escaped braces, return as is
    if "{" not in text or is_quoted(text):
        return [text]
    
    # Find outermost brace patterns
    pattern = r'{([^{}]*(?:{[^{}]*}[^{}]*)*?)}'
    match = re.search(pattern, text)
    
    if not match:
        return [text]
    
    # Extract the parts
    prefix = text[:match.start()]
    brace_content = match.group(1)
    suffix = text[match.end():]
    
    # Process the content (handle commas or ranges)
    if '..' in brace_content and ',' not in brace_content:
        # Range expansion
        parts = handle_range(brace_content)
    else:
        # Comma-separated expansion
        parts = handle_comma_parts(brace_content)
    
    # Generate the results
    results = []
    for part in parts:
        # Recursively handle nested braces
        expanded = expand_braces(prefix + part + suffix)
        results.extend(expanded)
    
    return results
```

## Integration into Expansion Process

```python
def expand_all(text: str) -> str:
    """Perform all expansions on text."""
    # Handle quotes properly
    if text.startswith("'") and text.endswith("'"):
        # Single quotes prevent all expansion and are removed
        return text[1:-1]
    
    # NEW: Brace expansion first (unless quoted)
    if '{' in text and not (text.startswith("'") and text.endswith("'")):
        expanded = expand_braces(text)
        # Process each expansion result separately
        results = [expand_all(item) for item in expanded]
        return ' '.join(results)
    
    # Continue with other expansions as before...
```

## Testing Strategy

Create a test file `tests/test_parser/test_brace_expansion.py` with test cases for:

1. Basic comma-separated patterns
2. Numeric and alphabetic ranges
3. Nested braces
4. Quoting rules
5. Edge cases
6. Interaction with other expansion types

Each test should verify that the output of brace expansion matches the expected result, similar to other expansion test patterns in the codebase.