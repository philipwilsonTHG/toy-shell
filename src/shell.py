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
    
    def __init__(self, debug_mode=False):
        self.interactive = sys.stdin.isatty()
        self.debug_mode = debug_mode
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
            
            # Handle history execution with ! prefix
            if line.startswith('!'):
                if len(line) > 1:
                    # If it's a number, execute that history entry
                    history_num_str = line[1:]
                    try:
                        history_num = int(history_num_str)
                        history_cmd = HistoryManager.get_command_by_number(history_num)
                        if history_cmd:
                            print(history_cmd)  # Echo the command
                            return self.execute_line(history_cmd)
                        else:
                            print(f"!{history_num_str}: event not found", file=sys.stderr)
                            return 1
                    except ValueError:
                        print(f"!{history_num_str}: event not found", file=sys.stderr)
                        return 1
                else:
                    print("!: event not found", file=sys.stderr)
                    return 1
                
            # Handle history command directly to prevent tokenizing and
            # attempting to execute as a normal command after the builtin
            if line == "history" or line.startswith("history "):
                args = line.split()[1:] if " " in line else []
                from .builtins.history import history
                history(*args)
                return 0
            
            # Try to parse using the AST parser
            if not hasattr(self, 'parser'):
                from .parser.parser import Parser
                self.parser = Parser()
                
            if not hasattr(self, 'ast_executor'):
                from .execution.ast_executor import ASTExecutor
                self.ast_executor = ASTExecutor(self.interactive, self.debug_mode)
            
            # Check if we have an incomplete parse from a previous line
            if self.parser.is_incomplete():
                # Use PS2 for continuation prompt
                node = self.parser.parse(line)
                if node:
                    # Successfully parsed, execute the AST
                    return self.ast_executor.execute(node)
                else:
                    # Still incomplete, wait for more input
                    return 0
            
            # Try parsing with the AST parser
            node = self.parser.parse(line)
            
            if node:
                # Successfully parsed an AST, execute it
                return self.ast_executor.execute(node)
            
            if self.parser.is_incomplete():
                # Need more input for a complete statement
                return 0
            
            # Fall back to the old tokenize and execute method
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
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return 1
    
    def run(self) -> int:
        """Main shell loop"""
        exit_status = 0
        
        while True:
            try:
                # Update job statuses
                self.job_manager.update_job_statuses()
                
                if self.interactive:
                    # Check if we're in a multi-line input state
                    if hasattr(self, 'parser') and self.parser.is_incomplete():
                        # Use continuation prompt (PS2)
                        prompt = "> "
                    else:
                        # Get primary prompt from shell context
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
                    if not self.interactive and not (hasattr(self, 'parser') and self.parser.is_incomplete()):
                        break
                    
            except EOFError:
                # Reset parser state if we were in the middle of a multi-line statement
                if hasattr(self, 'parser') and self.parser.is_incomplete():
                    self.parser.reset()
                print()
                break
            except KeyboardInterrupt:
                # Reset parser state if we were in the middle of a multi-line statement
                if hasattr(self, 'parser') and self.parser.is_incomplete():
                    self.parser.reset()
                print()
                continue
                
        return exit_status


def main():
    """Shell entry point"""
    # Process command line arguments
    debug_mode = False
    args = sys.argv[1:]
    
    # Check for help
    if "-h" in args or "--help" in args:
        print("Usage: psh [OPTIONS] [SCRIPT_FILE | -c COMMAND]")
        print("\nOptions:")
        print("  --debug       Enable debug mode (prints AST before execution)")
        print("  -h, --help    Show this help message and exit")
        print("  -c COMMAND    Execute the given command")
        print("\nExamples:")
        print("  psh --debug script.sh                 Run script with AST debugging")
        print("  psh --debug -c 'echo hello'           Run command with AST debugging")
        print("  psh -c 'for i in 1 2 3; do echo $i; done'   Run a for loop")
        return 0
    
    # Check for --debug flag
    if "--debug" in args:
        debug_mode = True
        args.remove("--debug")
    
    shell = Shell(debug_mode=debug_mode)
    
    # Handle command line arguments
    if args:
        # Handle -c option to execute a command
        if args[0] == "-c" and len(args) > 1:
            command = args[1]
            try:
                return shell.execute_line(command) or 0
            except Exception as e:
                print(f"Error running command: {e}", file=sys.stderr)
                if debug_mode:
                    import traceback
                    traceback.print_exc()
                return 1
        # Handle script file
        else:
            script_path = args[0]
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
