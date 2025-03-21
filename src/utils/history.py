#!/usr/bin/env python3

import os
import sys
import readline
import atexit
from typing import Optional, List
from ..context import SHELL

class HistoryManager:
    """Manages shell command history"""
    
    @staticmethod
    def init_history():
        """Initialize history management"""
        # Configure readline - initialize only what's needed for history
        # (completion settings are handled by the Completer class)
        
        # Key bindings for history navigation
        readline.parse_and_bind('"\\C-r": reverse-search-history')
        readline.parse_and_bind('"\\C-s": forward-search-history')
        
        # Arrow keys for history navigation
        readline.parse_and_bind('"\\C-p": previous-history')    # Ctrl+P (same as up arrow)
        readline.parse_and_bind('"\\C-n": next-history')        # Ctrl+N (same as down arrow)
        readline.parse_and_bind('up: previous-history')         # Up arrow 
        readline.parse_and_bind('down: next-history')           # Down arrow
        
        # Search with prefix 
        readline.parse_and_bind('"\\M-p": history-search-backward')  # Alt+P
        readline.parse_and_bind('"\\M-n": history-search-forward')   # Alt+N
        
        # Line navigation and editing
        readline.parse_and_bind('"\\C-f": forward-char')       # Ctrl+F (same as right arrow)
        readline.parse_and_bind('"\\C-b": backward-char')      # Ctrl+B (same as left arrow)
        readline.parse_and_bind('right: forward-char')         # Right arrow 
        readline.parse_and_bind('left: backward-char')         # Left arrow
        readline.parse_and_bind('"\\C-a": beginning-of-line')  # Move to start of line
        readline.parse_and_bind('"\\C-e": end-of-line')        # Move to end of line
        readline.parse_and_bind('"\\C-k": kill-line')          # Kill to end of line
        readline.parse_and_bind('"\\C-u": unix-line-discard')  # Kill whole line
        readline.parse_and_bind('"\\C-w": unix-word-rubout')   # Kill word backward
        readline.parse_and_bind('"\\C-y": yank')               # Paste killed text
        
        # Load history and register save on exit
        HistoryManager.load_history()
        atexit.register(HistoryManager.save_history)
    
    @staticmethod
    def get_command_by_number(num: int) -> Optional[str]:
        """Get a command from history by its number"""
        try:
            if 1 <= num <= readline.get_current_history_length():
                return readline.get_history_item(num)
            return None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def load_history():
        """Load history from file"""
        try:
            readline.read_history_file(SHELL.histfile)
            readline.set_history_length(SHELL.histsize)
        except FileNotFoundError:
            pass
    
    @staticmethod
    def save_history():
        """Save history to file"""
        try:
            readline.write_history_file(SHELL.histfile)
        except Exception as e:
            print(f"Failed to save history: {e}", file=sys.stderr)
    
    @staticmethod
    def get_history(start: Optional[int] = None, 
                    count: Optional[int] = None) -> List[str]:
        """Get history entries"""
        length = readline.get_current_history_length()
        if start is None:
            start = 1
        if count is None:
            count = length
        
        start = max(1, start)
        end = min(length + 1, start + count)
        
        return [readline.get_history_item(i) for i in range(start, end)]
        
    @staticmethod
    def get_next_index() -> int:
        """Get the next history index"""
        return readline.get_current_history_length() + 1
    
    @staticmethod
    def clear_history():
        """Clear history"""
        readline.clear_history()
        try:
            os.remove(SHELL.histfile)
        except FileNotFoundError:
            pass
    
    @staticmethod
    def delete_entry(pos: int) -> bool:
        """Delete history entry at position"""
        try:
            if 1 <= pos <= readline.get_current_history_length():
                readline.remove_history_item(pos - 1)
                return True
        except ValueError:
            pass
        return False
