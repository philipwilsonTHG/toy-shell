#!/usr/bin/env python3
"""
Brace expansion module for shell-like brace expansion.
This module has been extracted from the original expander.py to maintain
this functionality independent of the state machine expander.
"""

import re
from .quotes import is_in_single_quotes


def expand_braces(text: str) -> list:
    """Expand brace patterns in text.
    
    Handles patterns like {a,b,c} and ranges like {1..5} or {a..z}.
    Returns a list of expanded strings.
    
    According to POSIX:
    - Brace expansion is performed before any other expansions
    - Brace expansion is not performed on text in single quotes
    - Brace expansion can still occur within double quotes
    """
    # If no braces or escaped braces, return original text
    if '{' not in text or '\\{' in text:
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
    
    # Check if the opening brace is inside single quotes
    brace_start = len(prefix)
    if is_in_single_quotes(text, brace_start):
        # If brace is inside single quotes, don't expand it
        # But we still need to check for other braces in the remainder
        if '{' in remainder:
            result = []
            for expanded_remainder in expand_braces(remainder):
                result.append(f"{prefix}{brace_pattern}{middle_suffix}{expanded_remainder}")
            return result
        return [text]
    
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
    
    # Check if it's a range pattern like {1..5} or {1..5..2} or {a..z}
    # Match with optional step
    range_match = re.match(r'([^.]+)\.\.([^.]+)(?:\.\.([^.]+))?', brace_content)
    if range_match and ',' not in brace_content:
        # Extract start, end, and optional step
        if len(range_match.groups()) == 3:
            start, end, step_str = range_match.groups()
        else:
            start, end = range_match.groups()
            step_str = None
        
        # Numeric range
        if start.isdigit() and end.isdigit():
            start_val, end_val = int(start), int(end)
            
            # Parse step if present, otherwise use default step
            if step_str and step_str.isdigit() and int(step_str) > 0:
                step = int(step_str)
            else:
                step = 1 if start_val <= end_val else -1
                
            # For decreasing ranges with custom step, make step negative
            if start_val > end_val and step > 0:
                step = -step
                
            items = [str(i) for i in range(start_val, end_val + (1 if step > 0 else -1), step)]
        
        # Alphabetic range
        elif len(start) == 1 and len(end) == 1 and start.isalpha() and end.isalpha():
            start_val, end_val = ord(start), ord(end)
            
            # Parse step if present, otherwise use default step
            if step_str and step_str.isdigit() and int(step_str) > 0:
                step = int(step_str)
            else:
                step = 1 if start_val <= end_val else -1
                
            # For decreasing ranges with custom step, make step negative
            if start_val > end_val and step > 0:
                step = -step
                
            items = [chr(i) for i in range(start_val, end_val + (1 if step > 0 else -1), step)]
        
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