#!/usr/bin/env python3

"""
Dynamic prompt formatter for the shell
Provides variable expansion for prompt templates
"""

import os
import sys
import pwd
import socket
import subprocess
from typing import Dict, Any, Optional, Callable


class PromptFormatter:
    """Handles dynamic prompt formatting with various substitutions"""

    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bold': '\033[1m',
        'italic': '\033[3m',
        'underline': '\033[4m',
    }

    def __init__(self):
        """Initialize the prompt formatter"""
        self.cache: Dict[str, Any] = {}
        # Initialize with shared exit status if available
        self._last_exit_status = self.get_shared_exit_status()
        self._register_handlers()

    def set_exit_status(self, status: int) -> None:
        """Set the last command exit status"""
        self._last_exit_status = status
        # Singleton pattern - store the status in class variable
        PromptFormatter._shared_exit_status = status
        
    @classmethod
    def get_shared_exit_status(cls) -> int:
        """Get the shared exit status across formatter instances"""
        if not hasattr(cls, '_shared_exit_status'):
            cls._shared_exit_status = 0
        return cls._shared_exit_status

    def _register_handlers(self) -> None:
        """Register all prompt variable handlers"""
        self.handlers = {
            # User info
            'u': self._get_username,       # Username
            'h': self._get_hostname,       # Short hostname
            'H': self._get_fqdn,           # Full hostname
            '$': self._get_prompt_char,    # $ for regular users, # for root
            
            # Directory
            'w': self._get_cwd,            # Current working directory with ~ for $HOME
            'W': self._get_basename,       # Basename of current directory
            
            # Status
            '?': self._get_exit_status,    # Exit status with color
            'e': lambda: str(self._last_exit_status),  # Raw exit status
            
            # Time
            't': self._get_time,           # Current time (HH:MM:SS)
            'T': self._get_time_12h,       # Current time in 12h format
            'd': self._get_date,           # Current date
            
            # Git
            'g': self._get_git_branch,     # Current git branch if in a repo
            
            # Jobs
            'j': self._get_job_count,      # Number of jobs

            # History
            '!': self._get_history_number, # History number
            
            # Environment
            'v': self._get_virtualenv,     # Python virtualenv
        }

    def format(self, template: str) -> str:
        """
        Format a prompt template with dynamic elements
        
        Supported variables:
        - \\u: Username
        - \\h: Hostname (short)
        - \\H: Hostname (FQDN)
        - \\w: Current working directory
        - \\W: Basename of current directory
        - \\$: # for root, $ for regular user
        - \\?: Exit status (colored)
        - \\e: Raw exit status
        - \\t: Current time (HH:MM:SS)
        - \\T: Current time (12-hour)
        - \\d: Current date
        - \\g: Git branch
        - \\j: Number of jobs
        - \\!: History number
        - \\v: Python virtualenv
        
        Color codes:
        - \\[COLOR]: Start color (e.g. \\[red])
        - \\[reset]: Reset color
        """
        result = ""
        i = 0
        while i < len(template):
            if template[i] == '\\' and i + 1 < len(template):
                # Handle escape sequence
                i += 1
                if template[i] == '\\':
                    # Literal backslash
                    result += '\\'
                elif template[i] == '[':
                    # Color code
                    end = template.find(']', i)
                    if end != -1:
                        color_name = template[i+1:end].lower()
                        if color_name in self.COLORS:
                            result += self.COLORS[color_name]
                        i = end
                    else:
                        # Unclosed color tag, add as is
                        result += '\\['
                elif template[i] in self.handlers:
                    # Call the appropriate handler
                    result += self.handlers[template[i]]()
                else:
                    # Unknown escape sequence, pass through
                    result += '\\' + template[i]
            else:
                result += template[i]
            i += 1
                
        return result

    def _get_username(self) -> str:
        """Get current username"""
        if 'username' not in self.cache:
            self.cache['username'] = pwd.getpwuid(os.getuid()).pw_name
        return self.cache['username']
    
    def _get_hostname(self) -> str:
        """Get short hostname"""
        if 'hostname' not in self.cache:
            self.cache['hostname'] = socket.gethostname().split('.')[0]
        return self.cache['hostname']
    
    def _get_fqdn(self) -> str:
        """Get fully qualified domain name"""
        if 'fqdn' not in self.cache:
            self.cache['fqdn'] = socket.getfqdn()
        return self.cache['fqdn']
    
    def _get_prompt_char(self) -> str:
        """Return # for root, $ for normal user"""
        return '#' if os.getuid() == 0 else '$'
    
    def _get_cwd(self) -> str:
        """Get current working directory with ~ for $HOME"""
        home = os.path.expanduser("~")
        cwd = os.getcwd()
        if cwd.startswith(home):
            return '~' + cwd[len(home):]
        return cwd
    
    def _get_basename(self) -> str:
        """Get basename of current directory"""
        return os.path.basename(os.getcwd())
    
    def _get_exit_status(self) -> str:
        """Get colorized exit status"""
        if self._last_exit_status == 0:
            return f"{self.COLORS['green']}0{self.COLORS['reset']}"
        return f"{self.COLORS['red']}{self._last_exit_status}{self.COLORS['reset']}"
    
    def _get_time(self) -> str:
        """Get current time in 24h format"""
        import time
        return time.strftime("%H:%M:%S")
    
    def _get_time_12h(self) -> str:
        """Get current time in 12h format"""
        import time
        return time.strftime("%I:%M:%S %p")
    
    def _get_date(self) -> str:
        """Get current date"""
        import time
        return time.strftime("%Y-%m-%d")
    
    def _get_git_branch(self) -> str:
        """Get current git branch if in a repo"""
        try:
            # Cache this result to avoid running git repeatedly
            if 'git_branch' not in self.cache or self.cache['git_dir'] != os.getcwd():
                result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    capture_output=True,
                    text=True,
                    timeout=0.2,  # Short timeout to avoid hanging
                )
                if result.returncode == 0 and result.stdout.strip():
                    branch = result.stdout.strip()
                    self.cache['git_branch'] = f"({branch})"
                else:
                    self.cache['git_branch'] = ""
                self.cache['git_dir'] = os.getcwd()
            return self.cache['git_branch']
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            # Handle errors silently by returning nothing
            return ""
    
    def _get_job_count(self) -> str:
        """Get number of background jobs"""
        # Access job count from shell context
        try:
            from ..context import SHELL
            running_jobs = sum(1 for job in SHELL.jobs.values() 
                               if job.status.name == "RUNNING")
            if running_jobs > 0:
                return str(running_jobs)
            return "0"
        except (ImportError, AttributeError):
            return "0"
    
    def _get_history_number(self) -> str:
        """Get current history number"""
        try:
            from ..utils.history import HistoryManager
            return str(HistoryManager.get_next_index() - 1)
        except (ImportError, AttributeError):
            return "!"
    
    def _get_virtualenv(self) -> str:
        """Get Python virtualenv name if active"""
        venv = os.environ.get('VIRTUAL_ENV')
        if venv:
            return f"({os.path.basename(venv)})"
        return ""