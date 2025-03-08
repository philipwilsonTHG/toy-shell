#!/usr/bin/env python3

import os
import sys
import signal
from typing import Optional, List

from .context import SHELL
from .utils.terminal import TerminalController
from .utils.history import HistoryManager
from .utils.completion import Completer
from .parser.token_types import Token, TokenType, create_word_token
from .parser.lexer import tokenize
from .parser.parser.shell_parser import ShellParser
from .parser.expander import expand_variables
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
        
        # Initialize the new parser
        self.parser = ShellParser()
        
        # Track last command's exit status
        self.last_exit_status = 0
        
        # Flag to prevent infinite loops during test collection
        self.collecting_tests = os.environ.get('PYTEST_RUNNING') == '1'
        
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
            # Debug output
            if self.debug_mode:
                print(f"[DEBUG] Executing line: {line[:50]}{'...' if len(line) > 50 else ''}", file=sys.stderr)
                
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                return 0
            
            # Special handling for commands separated by semicolons
            if ';' in line:
                # Simple semicolon handling without accounting for quotes
                from .parser.quotes import handle_quotes
                
                # Preserve quotes when splitting on semicolons
                commands = []
                current_cmd = []
                in_single_quote = False
                in_double_quote = False
                
                for char in line:
                    if char == "'" and not in_double_quote:
                        in_single_quote = not in_single_quote
                        current_cmd.append(char)
                    elif char == '"' and not in_single_quote:
                        in_double_quote = not in_double_quote
                        current_cmd.append(char)
                    elif char == ';' and not (in_single_quote or in_double_quote):
                        if current_cmd:
                            commands.append(''.join(current_cmd).strip())
                            current_cmd = []
                    else:
                        current_cmd.append(char)
                
                # Add final command if any
                if current_cmd:
                    commands.append(''.join(current_cmd).strip())
                
                # Execute each command in sequence
                last_status = 0
                for cmd in commands:
                    if cmd:  # Skip empty commands
                        result = self.execute_line(cmd)
                        if result is not None:
                            last_status = result
                
                return last_status
                
            # Handle $? special variable expansion
            if "$?" in line:
                line = line.replace("$?", str(self.last_exit_status))
                
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
            
            # Initialize AST executor if not already done
            if not hasattr(self, 'ast_executor'):
                from .execution.ast_executor import ASTExecutor
                self.ast_executor = ASTExecutor(self.interactive, self.debug_mode)
            
            # Pre-process escaped variables for better compatibility
            # Handle '\$VAR' format (common in scripts) by replacing with '$VAR'
            if r'\$' in line:
                line = line.replace(r'\$', '$')
            
            # Check if we have an incomplete parse from a previous line
            if self.parser.is_incomplete():
                # Use PS2 for continuation prompt
                node = self.parser.parse_multi_line(line)
                if node:
                    # Successfully parsed, execute the AST
                    return self.ast_executor.execute(node)
                else:
                    # Still incomplete, wait for more input
                    return 0
            
            # Try parsing the line with the new parser
            # First tokenize the input to properly handle pipelines
            from .parser.lexer import tokenize
            tokens = tokenize(line)
            
            # Use tokens with parse method for better pipeline handling
            node = self.parser.parse(tokens)
            
            if self.debug_mode:
                print(f"[DEBUG] Parse result type: {type(node)}", file=sys.stderr)
            
            if node:
                # Successfully parsed an AST, execute it
                if self.debug_mode:
                    print(f"[DEBUG] Executing AST:", file=sys.stderr)
                    print(f"{node}", file=sys.stderr)
                    
                return self.ast_executor.execute(node)
            
            if self.parser.is_incomplete():
                # Need more input for a complete statement
                return 0
            
            # Fall back to the tokenize and execute method for simple commands
            # Check for background execution
            background = line.endswith('&')
            if background:
                line = line[:-1].strip()
            
            # Tokenize and execute
            tokens = tokenize(line)
            
            # Debug output
            if self.debug_mode:
                print("[DEBUG] Raw tokens:", file=sys.stderr)
                for i, token in enumerate(tokens):
                    print(f"  Token {i}: '{token.value}' ({token.token_type})", file=sys.stderr)
                
                # Debug the redirections
                from .parser.redirection import RedirectionParser
                cmd_tokens, redirections = RedirectionParser.parse_redirections(tokens)
                print("[DEBUG] Parsed redirections:", file=sys.stderr)
                for op, target in redirections:
                    print(f"  {op} -> {target}", file=sys.stderr)
                
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
        
        # If we're running in pytest collection mode, just return immediately
        if self.collecting_tests and not self.interactive:
            return 0
            
        while True:
            try:
                # Update job statuses
                self.job_manager.update_job_statuses()
                
                if self.interactive:
                    # Check if we're in a multi-line input state
                    if self.parser.is_incomplete():
                        # Use continuation prompt (PS2)
                        prompt = "> "
                    else:
                        # Get primary prompt from shell context
                        prompt = SHELL.get_prompt()
                        
                    line = input(prompt)
                else:
                    line = input()
                    
                result = self.execute_line(line)
                
                # Store the exit status for $? variable
                if result is not None:
                    self.last_exit_status = result
                    
                    # Set $? environment variable
                    os.environ["?"] = str(self.last_exit_status)
                
                    # Check for special exit code (-1000 to -1255) indicating explicit exit
                    if isinstance(result, list):
                        result = result[0]

                    if result <= -1000 and result >= -1255:
                        exit_status = abs(result) - 1000
                        break
                    else:
                        exit_status = result
                        
                    # Only exit for non-interactive mode after command completion
                    if not self.interactive and not self.parser.is_incomplete():
                        break
                    
            except EOFError:
                # Reset parser state if we were in the middle of a multi-line statement
                if self.parser.is_incomplete():
                    # For ShellParser, we need to reset context
                    self.parser = ShellParser()  # Create a new parser instance
                print()
                break
            except KeyboardInterrupt:
                # Reset parser state if we were in the middle of a multi-line statement
                if self.parser.is_incomplete():
                    # For ShellParser, we need to reset context
                    self.parser = ShellParser()  # Create a new parser instance
                print()
                continue
                
        return exit_status


def print_help():
    """Print usage information and exit"""
    print("Usage: psh [OPTIONS] [SCRIPT_FILE]")
    print("\nOptions:")
    print("  -c COMMAND    Execute the given command")
    print("  -d, --debug   Enable debug mode (prints AST before execution)")
    print("  -h, --help    Show this help message and exit")
    print("  -v, --version Display version information and exit")
    print("\nExamples:")
    print("  psh script.sh                           Run script")
    print("  psh -d script.sh                        Run script with debugging")
    print("  psh -c 'echo hello'                     Run a single command")
    print("  psh -c 'for i in 1 2 3; do echo $i; done'   Run a for loop")
    return 0

def print_version():
    """Print version information and exit"""
    from .builtins.core import version
    version()
    return 0

def execute_script(script_path, debug_mode=False):
    """Execute a shell script file"""
    try:
        with open(script_path) as f:
            # Read entire script
            script_content = f.read()
            
            # Create a special script execution shell
            script_shell = Shell(debug_mode=debug_mode)
            
            # Skip shebang line if present
            lines = script_content.split('\n')
            
            if lines and lines[0].startswith('#!'):
                if debug_mode:
                    print(f"[DEBUG] Skipping shebang line: {lines[0]}", file=sys.stderr)
                start_line = 1
            else:
                start_line = 0
            
            # Process script line by line, skipping comments and empty lines
            exit_status = 0
            for i in range(start_line, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('#'):
                    continue
                    
                if debug_mode:
                    print(f"[DEBUG] Executing script line {i+1}: {line}", file=sys.stderr)
                    
                try:
                    result = script_shell.execute_line(line)
                    if result is not None:
                        exit_status = result
                except Exception as e:
                    if debug_mode:
                        print(f"[DEBUG] Error executing line {i+1}: {e}", file=sys.stderr)
                    exit_status = 1
                    break
            
            return exit_status
    except FileNotFoundError:
        print(f"Error: Script file not found: {script_path}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Error: Permission denied when reading: {script_path}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running script {script_path}: {e}", file=sys.stderr)
        if debug_mode:
            import traceback
            traceback.print_exc()
        return 1

def main():
    """Shell entry point using getopts-style argument parsing"""
    import getopt
    import sys
    
    # Define options
    short_opts = "c:dhv"
    long_opts = ["debug", "help", "version"]
    
    # Default values
    debug_mode = False
    command = None
    script_path = None
    
    try:
        # Parse command line options
        opts, args = getopt.getopt(sys.argv[1:], short_opts, long_opts)
        
        # Process options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                return print_help()
            elif opt in ("-v", "--version"):
                return print_version()
            elif opt in ("-d", "--debug"):
                debug_mode = True
            elif opt == "-c":
                command = arg
    
        # Create shell instance with appropriate debug setting
        shell = Shell(debug_mode=debug_mode)
        
        # Store shell instance in a global variable for the source builtin to access
        sys.modules["__main__"].shell = shell
        
        # Handle command if provided with -c
        if command is not None:
            try:
                return shell.execute_line(command) or 0
            except Exception as e:
                print(f"Error running command: {e}", file=sys.stderr)
                if debug_mode:
                    import traceback
                    traceback.print_exc()
                return 1
        
        # Handle script file if provided as positional argument
        if args:
            script_path = args[0]
            return execute_script(script_path, debug_mode)
        
        # No command or script provided, run in interactive mode
        return shell.run()
        
    except getopt.GetoptError as e:
        # Handle invalid options
        print(f"Error: {e}", file=sys.stderr)
        print("Use --help for usage information", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
