#!/usr/bin/env python3

import os
import sys
import re
from typing import Optional, List

from .context import SHELL
from .utils.terminal import TerminalController
from .utils.history import HistoryManager
from .utils.completion import Completer
from .parser.token_types import Token, TokenType, create_word_token
from .parser.lexer import tokenize
from .parser.parser.shell_parser import ShellParser
from .parser.state_machine_expander import StateMachineExpander
from .parser.state_machine_adapter import StateMachineWordExpander
from .parser import expand_variables, expand_all, expand_braces, expand_command_substitution, expand_tilde, expand_wildcards, expand_arithmetic
from .config.manager import ConfigManager
from .execution.pipeline import PipelineExecutor
from .execution.job_manager import JobManager
from .builtins.special_variables import SPECIAL_VARS, register_special_variable_handler


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
        
        # Initialize prompt formatter
        from .utils.prompt import PromptFormatter
        self.prompt_formatter = PromptFormatter()
        
        # Initialize word expander for faster variable expansion
        # Create a scope provider that handles special variables
        self.scope_provider = lambda name: os.environ.get(name)
        
        # Initialize special variables handler
        SPECIAL_VARS.set_script_name("psh")
        
        # Create an enhanced scope provider that checks for special variables
        enhanced_scope_provider = register_special_variable_handler(self.scope_provider)
        
        # Initialize word expander with the enhanced scope provider
        self.word_expander = StateMachineWordExpander(
            scope_provider=enhanced_scope_provider,
            debug_mode=debug_mode
        )
        
        # Initialize AST executor early to make function registry available
        from .execution.ast_executor import ASTExecutor
        self.ast_executor = ASTExecutor(self.interactive, self.debug_mode)
        
        # Register this shell instance with the global context
        SHELL.set_current_shell(self)
        
        if self.interactive:
            # Set up job control
            TerminalController.setup_job_control()
            
            # First set up completion (this needs to configure readline)
            self.completer = Completer()
            
            # Then set up history (will use readline already configured by completer)
            HistoryManager.init_history()
            
    def _preprocess_multiline_script(self, script_content: str) -> str:
        """
        Preprocess a multiline script to handle control structures properly.
        
        This converts multiline if/while/for statements into single-line equivalents
        that can be parsed correctly.
        """
        lines = script_content.split('\n')
        processed_lines = []
        i = 0
        
        # Helper to check if a line starts a control structure
        def is_control_start(line):
            line = line.strip()
            return (line.startswith('if ') or line == 'if' or
                   line.startswith('while ') or line == 'while' or
                   line.startswith('for ') or line == 'for' or
                   line.startswith('until ') or line == 'until' or
                   line.startswith('case ') or line == 'case')
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                processed_lines.append(line)
                i += 1
                continue
                
            # Check if this starts a control structure
            if is_control_start(line):
                control_type = line.split()[0] if ' ' in line else line
                end_keyword = {'if': 'fi', 'while': 'done', 'for': 'done', 'until': 'done', 'case': 'esac'}[control_type]
                
                # Gather the entire structure
                structure_lines = [line]
                depth = 1
                j = i + 1
                
                while j < len(lines) and depth > 0:
                    next_line = lines[j].strip()
                    
                    # Skip comments but preserve empty lines
                    if next_line.startswith('#'):
                        j += 1
                        continue
                        
                    # Include this line
                    if next_line:  # Only include non-empty lines
                        structure_lines.append(next_line)
                    
                    # Check for nested structures
                    if is_control_start(next_line):
                        if next_line.split()[0] if ' ' in next_line else next_line == control_type:
                            depth += 1
                    
                    # Check for end keywords
                    if next_line == end_keyword or next_line.endswith(' ' + end_keyword):
                        depth -= 1
                        
                    j += 1
                
                # Convert the structure to a single line with proper semicolons
                single_line = self._convert_structure_to_single_line(structure_lines)
                processed_lines.append(single_line)
                
                # Skip ahead
                i = j
            else:
                # Regular line, just add it
                processed_lines.append(line)
                i += 1
                
        return '\n'.join(processed_lines)
    
    def _convert_structure_to_single_line(self, lines):
        """Convert a multiline control structure to a single line with proper semicolons."""
        result = ""
        need_semicolon = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a standalone keyword
            is_keyword = line in ['then', 'else', 'elif', 'do', 'done', 'fi', 'esac']
            
            # Add semicolon before keywords if needed
            if need_semicolon and is_keyword:
                result += "; "
                
            # Add the current line
            if result and not result.endswith('; ') and not is_keyword:
                result += "; "
                
            result += line
            
            # Update state for next line
            need_semicolon = not is_keyword and not line.endswith(';')
            
        return result
        
    def _execute_single_line(self, line):
        """Execute a single line of shell code (internal implementation)."""
        # This is the part of execute_line that handles a single line
        # Process direct commands without recursive calls
        from .parser.lexer import tokenize
        
        # Skip empty or comment lines
        if not line or line.startswith('#'):
            return 0
            
        # Direct parsing and execution
        tokens = tokenize(line)
        node = self.parser.parse(tokens)
        
        if node:
            if self.debug_mode:
                print(f"[DEBUG] Executing parsed node: {type(node)}", file=sys.stderr)
            return self.ast_executor.execute(node)
        else:
            # Fall back to pipeline execution for simple commands
            if self.debug_mode:
                print(f"[DEBUG] Falling back to pipeline execution", file=sys.stderr)
            tokens = tokenize(line)
            return self.pipeline_executor.execute_pipeline(tokens, line.endswith('&'))
    
    def execute_line(self, line: str) -> Optional[int]:
        """Execute a line of input"""
        try:
            # Debug output
            if self.debug_mode:
                preview = line[:50] + ('...' if len(line) > 50 else '')
                print(f"[DEBUG] Executing line: {preview}", file=sys.stderr)
                
            # Special handling for multiline script content
            if '\n' in line:
                # For safety, we need to be smarter about handling multiline scripts
                # Let's pre-process the full script to convert it to a series of single-line commands
                
                # First, join the lines while preserving structure
                preprocessed_script = self._preprocess_multiline_script(line)
                
                # Now execute the preprocessed script which should have all structures converted to single lines
                if self.debug_mode:
                    print(f"[DEBUG] Preprocessed script: {preprocessed_script[:100]}...", file=sys.stderr)
                    
                # Process the preprocessed script line by line
                result = 0
                script_lines = preprocessed_script.split('\n')
                for script_line in script_lines:
                    if script_line.strip() and not script_line.strip().startswith('#'):
                        if self.debug_mode:
                            print(f"[DEBUG] Processing: {script_line[:50]}...", file=sys.stderr)
                        try:
                            # Process commands sequentially
                            current_result = self._execute_single_line(script_line.strip())
                            if current_result is not None:
                                result = current_result
                        except Exception as e:
                            if self.debug_mode:
                                print(f"[DEBUG] Error executing line: {e}", file=sys.stderr)
                            return 1
                
                return result
                
            # Skip empty lines and comments (for single lines)
            line = line.strip()
            if not line or line.startswith('#'):
                return 0
                
            # Reset prompt formatter with latest exit status
            if hasattr(self, 'last_exit_status'):
                self.prompt_formatter.set_exit_status(self.last_exit_status)
                
            # Make config_manager available to builtins
            from .context import SHELL
            SHELL._config_manager = self.config_manager
            
            # Special handling for function definitions
            # Don't split function definitions on semicolons
            stripped_line = line.lstrip()
            if stripped_line.startswith('function ') and '{' in line and '}' in line:
                # Let the parser handle the entire function definition
                if self.debug_mode:
                    print(f"[DEBUG] Detected function definition, passing to parser as single unit", file=sys.stderr)
                # Pass the entire function declaration to the parser
                pass
            # Special handling for commands separated by semicolons
            elif ';' in line:
                # Check if the line starts with a shell keyword or contains control structure keywords
                # Skip semicolon splitting for control structures
                shell_keywords = ['if', 'while', 'until', 'for', 'case']
                control_keywords = ['then', 'else', 'elif', 'fi', 'do', 'done', 'esac']
                has_control_structure = False
                
                # Check if the line starts with a keyword
                for keyword in shell_keywords:
                    if stripped_line.startswith(keyword + ' ') or stripped_line == keyword:
                        has_control_structure = True
                        break
                
                # Also check for control structure keywords that might be in the middle
                if not has_control_structure:
                    for keyword in control_keywords:
                        # Make sure we're looking for whole words with spaces or semicolons around them
                        if f" {keyword} " in line or f"{keyword} " in line or f" {keyword};" in line:
                            has_control_structure = True
                            break
                
                # If it's a control structure, don't split on semicolons
                if has_control_structure:
                    # Let the parser handle the entire statement
                    if self.debug_mode:
                        print(f"[DEBUG] Detected control structure, not splitting on semicolons", file=sys.stderr)
                    pass
                else:
                    # Simple semicolon handling without accounting for quotes
                    from .parser.quotes import handle_quotes
                    
                    # Preserve quotes and braces when splitting on semicolons
                    commands = []
                    current_cmd = []
                    in_single_quote = False
                    in_double_quote = False
                    brace_depth = 0  # Track nested braces
                    
                    for char in line:
                        # Handle quotes
                        if char == "'" and not in_double_quote:
                            in_single_quote = not in_single_quote
                            current_cmd.append(char)
                        elif char == '"' and not in_single_quote:
                            in_double_quote = not in_double_quote
                            current_cmd.append(char)
                        # Handle braces
                        elif char == '{' and not (in_single_quote or in_double_quote):
                            brace_depth += 1
                            current_cmd.append(char)
                        elif char == '}' and not (in_single_quote or in_double_quote):
                            brace_depth -= 1
                            current_cmd.append(char)
                        # Handle semicolons
                        elif char == ';' and not (in_single_quote or in_double_quote) and brace_depth == 0:
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
                
            # Handle special variables in the line
            if any(special_var in line for special_var in ["$?", "$$", "$!", "$-", "$0", "$#", "$*", "$@"]):
                # Special handling for $$ (PID)
                if "$$" in line:
                    line = line.replace("$$", str(os.getpid()))
                
                # Special handling for $0 (script name)
                if "$0" in line:
                    line = line.replace("$0", SPECIAL_VARS.get_script_name())
                
                # Special handling for $? (exit status)
                if "$?" in line:
                    line = line.replace("$?", str(self.last_exit_status))
                
                # Special handling for $! (background PID)
                if "$!" in line:
                    line = line.replace("$!", SPECIAL_VARS.get_last_bg_pid())
                
                # Special handling for $- (shell options)
                if "$-" in line:
                    line = line.replace("$-", SPECIAL_VARS.get_shell_options())
                
                # Special handling for $# (argument count)
                if "$#" in line:
                    line = line.replace("$#", str(len(SPECIAL_VARS._positional_params)))
                
                # Special handling for $* and $@ (arguments)
                if "$*" in line:
                    line = line.replace("$*", " ".join(SPECIAL_VARS._positional_params))
                
                if "$@" in line:
                    line = line.replace("$@", " ".join(SPECIAL_VARS._positional_params))
                
                # Handle positional parameters ($1, $2, etc.)
                for i in range(1, 10):
                    var = f"${i}"
                    if var in line:
                        line = line.replace(var, SPECIAL_VARS.get_positional_param(i))
                
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
            
            # AST executor is already initialized during __init__
            
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
                    
                    # Update prompt formatter with new exit status
                    self.prompt_formatter.set_exit_status(self.last_exit_status)
                    
                    # Set $? environment variable (for backward compatibility)
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
        # Use bash directly to execute the script for maximum compatibility
        if os.path.exists("/bin/bash") or os.path.exists("/usr/bin/bash"):
            os.system(f"bash {script_path}")
            return 0
            
        # Fallback to using our shell with -c
        import subprocess
        
        with open(script_path) as f:
            # Read entire script
            script_content = f.read()
            
        # Execute with -c for simplicity
        cmd = [sys.executable, "-m", "src.shell", "-c", script_content]
        result = subprocess.run(cmd, check=False)
        return result.returncode
            
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