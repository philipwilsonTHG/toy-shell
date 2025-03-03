#!/usr/bin/env python3

import os
import sys
import glob
import readline
from typing import List, Optional

from ..builtins import BUILTINS


class Completer:
    """Handles command completion"""
    
    def __init__(self):
        self._current_completions: List[str] = []
        self._setup_completion()
    
    def _setup_completion(self):
        """Set up readline completion"""
        # Set the completer function
        readline.set_completer(self._complete)
        
        # Set completion delimiter characters
        readline.set_completer_delims(' \t\n`!@#$%^&*()-=+[{]}\\|;:\'",<>?')
        
        # Configure readline completion behavior
        readline.parse_and_bind("set editing-mode emacs")
        readline.parse_and_bind("set completion-ignore-case on")
        readline.parse_and_bind("set show-all-if-ambiguous on")
        readline.parse_and_bind("set mark-symlinked-directories on")
        
        # Bind TAB key to completion
        try:
            # This is the macOS/BSD-specific binding
            if sys.platform == 'darwin':
                readline.parse_and_bind("bind ^I rl_complete") 
            else:
                # This is the Linux/GNU readline binding
                readline.parse_and_bind("tab: complete")
        except Exception:
            # Fallback to basic binding if specific platform bindings fail
            readline.parse_and_bind("tab: complete")
    
    def _complete(self, text: str, state: int) -> Optional[str]:
        """Readline completion function"""
        if state == 0:
            # Get current line
            line = readline.get_line_buffer()
            begin = readline.get_begidx()
            end = readline.get_endidx()
            
            # Get word being completed
            word = line[begin:end]
            
            # Get completions
            self._current_completions = self.complete_word(line, word)
        
        # Return next completion
        try:
            return self._current_completions[state]
        except IndexError:
            return None
    
    def complete_word(self, line: str, word: str) -> List[str]:
        """Complete a word based on context"""
        # First word - complete commands
        if not ' ' in line[:line.rfind(word) if word in line else len(line)]:
            return self._get_command_completions(word)
        
        # If word starts with $, complete environment variables
        if word.startswith('$'):
            return self._get_variable_completions(word[1:])
        
        # Complete files and directories
        return self._get_path_completions(word)
    
    def _get_command_completions(self, prefix: str) -> List[str]:
        """Get command completions from PATH and builtins"""
        completions = []
        
        # Add builtins
        for cmd in BUILTINS:
            if cmd.startswith(prefix):
                completions.append(cmd)
                
        # Get all directories in PATH
        paths = os.environ.get('PATH', '').split(':')
        
        # Add current directory
        paths.append('.')
        
        # Search each directory for matching executables
        for path in paths:
            if not path:
                continue
                
            pattern = os.path.join(path, prefix + '*')
            for match in glob.glob(pattern):
                if os.access(match, os.X_OK):
                    # Add just the command name, not full path
                    completions.append(os.path.basename(match))
        
        return sorted(set(completions))
    
    def _get_variable_completions(self, prefix: str) -> List[str]:
        """Complete environment variable names"""
        completions = []
        
        for var in os.environ:
            if var.startswith(prefix):
                completions.append('$' + var)
        
        return sorted(completions)
    
    def _get_path_completions(self, prefix: str) -> List[str]:
        """Get path completions"""
        # Handle tilde expansion
        if prefix.startswith('~'):
            expanded = os.path.expanduser(prefix)
            if expanded != prefix:
                prefix = expanded
        
        # Get directory and partial name
        directory = os.path.dirname(prefix) if prefix else '.'
        if not directory:
            directory = '.'
        partial = os.path.basename(prefix)
        
        # Get matches
        try:
            pattern = os.path.join(directory, partial + '*')
            matches = glob.glob(pattern)
            
            # Add trailing slash to directories
            completions = []
            for match in matches:
                if os.path.isdir(match):
                    completions.append(match + '/')
                else:
                    completions.append(match)
            
            return sorted(completions)
        except OSError:
            return []


# For backward compatibility
def get_command_completions(prefix: str) -> List[str]:
    """Get command completions from PATH"""
    completer = Completer()
    return completer._get_command_completions(prefix)


def get_path_completions(prefix: str) -> List[str]:
    """Get path completions"""
    completer = Completer()
    return completer._get_path_completions(prefix)


def complete_word(line: str, word: str) -> List[str]:
    """Complete a word in the command line
    
    Args:
        line: Full command line
        word: Word being completed
        
    Returns:
        List of possible completions
    """
    completer = Completer()
    return completer.complete_word(line, word)