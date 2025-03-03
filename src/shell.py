#!/usr/bin/env python3

import os
import sys
import signal
from typing import Optional, List

from .context import SHELL
from .utils.terminal import TerminalController
from .utils.history import HistoryManager
from .utils.completion import Completer
from .parser.lexer import Token, tokenize
from .config.manager import ConfigManager
from .execution.pipeline import PipelineExecutor
from .execution.job_manager import JobManager


class Shell:
    """Main shell implementation"""
    
    def __init__(self):
        self.interactive = sys.stdin.isatty()
        self.config_manager = ConfigManager()
        self.job_manager = JobManager()
        self.pipeline_executor = PipelineExecutor(self.interactive)
        
        if self.interactive:
            # Set up job control
            TerminalController.setup_job_control()
            
            # First set up completion (this needs to configure readline)
            self.completer = Completer()
            
            # Then set up history (will use readline already configured by completer)
            HistoryManager.init_history()
            
    def execute_line(self, line: str) -> Optional[int]:
        """Execute a line of input"""
        try:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                return 0
                
            # Handle version command directly
            if line == "version":
                from . import __version__
                print(f"Python Shell version {__version__}")
                print(f"Python {sys.version}")
                return 0
                
            # Handle history command directly to prevent tokenizing and
            # attempting to execute as a normal command after the builtin
            if line == "history" or line.startswith("history "):
                args = line.split()[1:] if " " in line else []
                from .builtins.history import history
                history(*args)
                return 0
            
            # Check for background execution
            background = line.endswith('&')
            if background:
                line = line[:-1].strip()
            
            # Tokenize and execute
            tokens = tokenize(line)
            result = self.pipeline_executor.execute_pipeline(tokens, background)
            
            # Ensure we return a value, not None (which causes shell to exit)
            if result is None:
                return 0
            return result
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def run(self) -> int:
        """Main shell loop"""
        exit_status = 0
        
        while True:
            try:
                # Update job statuses
                self.job_manager.update_job_statuses()
                
                if self.interactive:
                    # Get prompt from shell context
                    prompt = SHELL.get_prompt()
                    line = input(prompt)

                else:
                    line = input()
                    
                result = self.execute_line(line)
            
                if result is not None:
                    # Check for special exit code (-1000 to -1255) indicating explicit exit
                    if result <= -1000 and result >= -1255:
                        exit_status = abs(result) - 1000
                        break
                    else:
                        exit_status = result
                        
                    # Only exit for non-interactive mode after command completion
                    if not self.interactive:
                        break
                    
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue
                
        return exit_status


def main():
    """Shell entry point"""
    shell = Shell()
    
    # Handle script file
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        try:
            with open(script_path) as f:
                for line in f:
                    shell.execute_line(line)
            return 0
        except Exception as e:
            print(f"Error running script {script_path}: {e}", file=sys.stderr)
            return 1
    
    # Interactive mode
    return shell.run()


if __name__ == "__main__":
    sys.exit(main())
