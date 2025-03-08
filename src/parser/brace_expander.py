#!/usr/bin/env python3
"""
Brace expansion module for shell-like brace expansion.
This module has been extracted from the original expander.py to maintain
this functionality independent of the state machine expander.
"""

import re
from .quotes import is_quoted


def expand_braces(text: str) -> list:
    """Expand brace patterns in text.
    
    Handles patterns like {a,b,c} and ranges like {1..5} or {a..z}.
    Returns a list of expanded strings.
    """
    # If no braces or escaped braces, return original text
    if '{' not in text or '\\{' in text or is_quoted(text):
        return [text]
    
    # Special cases
    if text == "{}" or text == "{single}":
        return [text]
    
    # Find leftmost outermost brace pattern
    pattern = r'([^{]*)(\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\})([^{]*)(.*)'
    match = re.search(pattern, text)
    
    if not match:
        return [text]
    
    prefix = match.group(1)
    brace_pattern = match.group(2)  # The entire {x,y,z} pattern
    brace_content = match.group(3)  # Just the x,y,z content
    middle_suffix = match.group(4)  # Content after this brace but before any other braces
    remainder = match.group(5)      # Any remaining text that might contain more braces
    
    # Full suffix is everything after the current brace pattern
    suffix = middle_suffix + remainder
    
    # No expansion for empty braces or single-item (no commas)
    if not brace_content or (',' not in brace_content and '..' not in brace_content):
        # If there's more text with potential braces, process it recursively
        if '{' in remainder:
            result = []
            for expanded_remainder in expand_braces(remainder):
                result.append(f"{prefix}{brace_pattern}{middle_suffix}{expanded_remainder}")
            return result
        return [text]
    
    expanded = []
    
    # Check if it's a range pattern like {1..5} or {a..z}
    range_match = re.match(r'([^.]+)\.\.([^.]+)', brace_content)
    if range_match and ',' not in brace_content:
        start, end = range_match.groups()
        
        # Numeric range
        if start.isdigit() and end.isdigit():
            start_val, end_val = int(start), int(end)
            step = 1 if start_val <= end_val else -1
            items = [str(i) for i in range(start_val, end_val + step, step)]
        
        # Alphabetic range
        elif len(start) == 1 and len(end) == 1 and start.isalpha() and end.isalpha():
            start_val, end_val = ord(start), ord(end)
            step = 1 if start_val <= end_val else -1
            items = [chr(i) for i in range(start_val, end_val + step, step)]
        
        # Not a valid range
        else:
            return [text]
    else:
        # Handle normal comma-separated list, respecting nested braces
        items = []
        item_start = 0
        nesting_level = 0
        
        for i, char in enumerate(brace_content):
            if char == '{':
                nesting_level += 1
            elif char == '}':
                nesting_level -= 1
            elif char == ',' and nesting_level == 0:
                items.append(brace_content[item_start:i])
                item_start = i + 1
        
        # Add the last item
        items.append(brace_content[item_start:])
    
    # Generate expanded strings
    for item in items:
        # For each item in the current brace expansion
        new_text = f"{prefix}{item}{suffix}"
        # Recursively expand any remaining brace patterns in the entire resulting string
        for expanded_text in expand_braces(new_text):
            expanded.append(expanded_text)
    
    return expanded if expanded else [text]