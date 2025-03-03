#!/usr/bin/env python3

import sys
from typing import Optional
from ..utils.history import HistoryManager

def history(*args: str) -> None:
    """Display or manipulate command history
    
    Usage:
        history         # Display all history entries
        history N      # Display last N entries
        history -c     # Clear history
        history -d N   # Delete history entry N
    """
    if not args:
        # Display all history with line numbers
        entries = HistoryManager.get_history()
        for i, entry in enumerate(entries, 1):
            print(f"{i:4d}  {entry}")
        return

    cmd = args[0]
    if cmd == "-c":
        # Clear history
        HistoryManager.clear_history()
        return
    
    elif cmd == "-d" and len(args) > 1:
        # Delete specific history entry
        try:
            pos = int(args[1])
            if not HistoryManager.delete_entry(pos):
                sys.stderr.write(f"history: invalid position {args[1]}\n")
        except ValueError:
            sys.stderr.write(f"history: invalid position {args[1]}\n")
        return
    
    elif cmd.startswith('-'):
        sys.stderr.write(f"history: invalid option: {cmd}\n")
        sys.stderr.write("Usage: history [-c] [-d pos] [n]\n")
        return
    
    # Show last N entries
    try:
        n = int(cmd)
        if n < 1:
            sys.stderr.write("history: invalid number\n")
            return
        
        entries = HistoryManager.get_history()
        if not entries:
            return
            
        # Get last N entries
        start_idx = max(0, len(entries) - n)
        selected = entries[start_idx:]
        
        # Display with correct numbering
        start_num = start_idx + 1
        for i, entry in enumerate(selected, start_num):
            print(f"{i:4d}  {entry}")
    except ValueError:
        sys.stderr.write(f"history: invalid number: {cmd}\n")
