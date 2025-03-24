#!/usr/bin/env python3
"""
Utility functions for shell pattern handling.
"""

import re
from typing import List


def shell_pattern_to_regex(pattern: str) -> str:
    """Convert shell wildcard pattern to regular expression pattern
    
    Args:
        pattern: The shell pattern with wildcards
        
    Returns:
        Equivalent regex pattern
    """
    # Handle special cases directly
    if pattern == '*/':
        return '.*?/'  # Non-greedy match for any characters followed by a slash
    elif pattern == '.*':
        return '\\.[^.]*'  # Match a dot followed by any non-dot characters
    
    # Process the pattern character by character
    result = []
    i = 0
    in_char_class = False
    
    while i < len(pattern):
        char = pattern[i]
        
        if char == '*':
            # * matches any sequence (non-greedy by default)
            result.append('.*?')
        elif char == '?':
            # ? matches any single character
            result.append('.')
        elif char == '[' and not in_char_class:
            # Start of character class
            in_char_class = True
            result.append('[')
            
            # Check for negation
            if i + 1 < len(pattern) and pattern[i + 1] == '!':
                result.append('^')
                i += 1
        elif char == ']' and in_char_class:
            # End of character class
            in_char_class = False
            result.append(']')
        elif char == '\\':
            # Escape the next character
            if i + 1 < len(pattern):
                i += 1
                # Escape special regex characters
                next_char = pattern[i]
                if next_char in '.^$*+?()[]{}|\\':
                    result.append('\\' + next_char)
                else:
                    result.append(next_char)
        else:
            # Regular character - escape if it's a regex special character
            if char in '.^$+?(){}|\\' and not in_char_class:
                result.append('\\' + char)
            else:
                result.append(char)
        
        i += 1
    
    return ''.join(result)


def split_brace_pattern(pattern: str) -> List[str]:
    """Split a brace pattern by commas, respecting nested braces"""
    items = []
    item_start = 0
    brace_level = 0
    
    for i, char in enumerate(pattern):
        if char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
        elif char == ',' and brace_level == 0:
            # Found a comma at the top level
            items.append(pattern[item_start:i])
            item_start = i + 1
    
    # Add the last item
    items.append(pattern[item_start:])
    
    return items