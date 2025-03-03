#!/usr/bin/env python3

import os
import sys
import signal
import termios
import fcntl
from typing import Optional

class TerminalController:
    """Handles terminal control operations"""
    
    @staticmethod
    def set_foreground_pgrp(pgrp: int):
        """Give terminal control to specified process group"""
        if not sys.stdin.isatty():
            return
        try:
            os.tcsetpgrp(sys.stdin.fileno(), pgrp)
        except OSError:
            pass
    
    @staticmethod
    def save_terminal_attrs() -> Optional[list]:
        """Save current terminal attributes"""
        if not sys.stdin.isatty():
            return None
        try:
            return termios.tcgetattr(sys.stdin.fileno())
        except termios.error:
            return None
    
    @staticmethod
    def restore_terminal_attrs(attrs: list):
        """Restore saved terminal attributes"""
        if not sys.stdin.isatty() or not attrs:
            return
        try:
            termios.tcsetattr(
                sys.stdin.fileno(),
                termios.TCSADRAIN,
                attrs
            )
        except termios.error:
            pass
    
    @staticmethod
    def setup_job_control():
        """Set up job control signal handling"""
        if not sys.stdin.isatty():
            return
            
        # Ignore terminal control signals in the shell to prevent it from stopping
        signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        signal.signal(signal.SIGTTIN, signal.SIG_IGN)
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        
        # Put shell in its own process group
        os.setpgrp()
        TerminalController.set_foreground_pgrp(os.getpgrp())
    
    @staticmethod
    def reset_signal_handlers():
        """Reset signal handlers to default in child processes.
        This is crucial for allowing Ctrl-Z to stop child processes."""
        signal.signal(signal.SIGINT, signal.SIG_DFL)   # Allow Ctrl-C
        signal.signal(signal.SIGQUIT, signal.SIG_DFL)  # Allow Ctrl-\
        signal.signal(signal.SIGTSTP, signal.SIG_DFL)  # Allow Ctrl-Z
        signal.signal(signal.SIGTTOU, signal.SIG_DFL)  # Terminal output control
        signal.signal(signal.SIGTTIN, signal.SIG_DFL)  # Terminal input control
        signal.signal(signal.SIGCONT, signal.SIG_DFL)  # Continue signal
