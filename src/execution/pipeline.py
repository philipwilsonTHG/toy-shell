#!/usr/bin/env python3

import os
import sys
import signal
import re
from typing import List, Tuple, Dict, Optional

from ..parser.token_types import Token, TokenType, create_word_token
from ..parser.redirection import RedirectionParser
from ..parser.state_machine_expander import StateMachineExpander
from ..parser import expand_variables, expand_all, expand_braces, expand_command_substitution, expand_tilde, expand_wildcards, expand_arithmetic
from ..context import SHELL, JobStatus
from ..utils.terminal import TerminalController
from ..builtins import BUILTINS
from ..builtins.special_variables import SPECIAL_VARS


class TokenExpander:
    """Handles expansion of tokens (variables, wildcards, etc.)"""
    
    def __init__(self):
        # Initialize the state machine expander directly
        self.expander = StateMachineExpander(os.environ.get, 
                                            os.environ.get('DEBUG_SHELL') is not None)
    
    def expand_token(self, token: Token) -> List[str]:
        """Expand a single token into a list of strings"""
        expanded_tokens = []
        
        if token.token_type == TokenType.SUBSTITUTION:
            # Handle command substitution
            expanded = self.expander.expand_command(token.value)
            if expanded:
                expanded_tokens.extend(expanded.split())
        else:
            # Check if the token is quoted first before any other expansion
            is_double_quoted = token.value.startswith('"') and token.value.endswith('"')
            is_single_quoted = token.value.startswith("'") and token.value.endswith("'")
            
            # Handle brace expansion first if not in single quotes
            if '{' in token.value and not is_single_quoted:
                # Directly use expand_braces to get the list of expansions
                braces_expanded = self.expander.expand_braces(token.value)
                
                # For debugging
                if os.environ.get('DEBUG_EXPANSION') or os.environ.get('DEBUG_SHELL'):
                    print(f"[EXP] Brace expansion: '{token.value}' → {braces_expanded}", 
                          file=sys.stderr)
                
                # For each brace expansion result, also do variable expansion
                for brace_item in braces_expanded:
                    # Now run other expansion steps, including variables
                    var_expanded = self.expander.expand(brace_item)
                    
                    # For debugging
                    if os.environ.get('DEBUG_EXPANSION') or os.environ.get('DEBUG_SHELL'):
                        print(f"[EXP] Variable expansion: '{brace_item}' → '{var_expanded}'", 
                              file=sys.stderr)
                    
                    # Handle wildcards (but not for quoted strings)
                    if '*' in var_expanded or '?' in var_expanded:
                        import glob
                        matches = glob.glob(var_expanded)
                        if matches:
                            expanded_tokens.extend(sorted(matches))
                        else:
                            expanded_tokens.append(var_expanded)
                    else:
                        # Check for word splitting
                        if ' ' in var_expanded and not is_double_quoted:
                            expanded_tokens.extend(var_expanded.split())
                        else:
                            expanded_tokens.append(var_expanded)
            else:
                # Handle other expansions including variables
                expanded = self.expander.expand_all_with_brace_expansion(token.value)
                
                # For debugging
                if os.environ.get('DEBUG_EXPANSION'):
                    print(f"[EXP] Token: '{token.value}' → '{expanded}' (dq: {is_double_quoted}, sq: {is_single_quoted})", 
                          file=sys.stderr)
                
                # Handle wildcards (but not for quoted strings)
                if not (is_double_quoted or is_single_quoted) and ('*' in expanded or '?' in expanded):
                    import glob
                    matches = glob.glob(expanded)
                    if matches:
                        expanded_tokens.extend(sorted(matches))
                    else:
                        expanded_tokens.append(expanded)
                else:
                    # For quoted strings, preserve the entire string as one token
                    # even if it contains spaces
                    if (is_double_quoted or is_single_quoted):
                        expanded_tokens.append(expanded)
                    else:
                        # For non-quoted strings, handle variable expansion and word splitting
                        if ' ' in expanded:
                            expanded_tokens.extend(expanded.split())
                        else:
                            expanded_tokens.append(expanded)
                
        return expanded_tokens
    
    def expand_tokens(self, tokens: List[Token]) -> List[str]:
        """Expand multiple tokens into a list of strings"""
        expanded_tokens = []
        
        for token in tokens:
            # Check if this is a quoted token that should be preserved whole
            is_quoted = (token.value.startswith('"') and token.value.endswith('"')) or \
                       (token.value.startswith("'") and token.value.endswith("'"))
                       
            if is_quoted:
                # For quoted tokens, strip quotes and add as a single token
                from ..parser.quotes import strip_quotes
                expanded_tokens.append(strip_quotes(token.value))
            else:
                # For normal tokens, use standard expansion which may split on spaces
                expanded_tokens.extend(self.expand_token(token))
                
        return expanded_tokens


class RedirectionHandler:
    """Handles file redirections for commands"""
    
    def __init__(self):
        # Constants for file opening modes
        self.O_WRONLY = os.O_WRONLY
        self.O_CREAT = os.O_CREAT
        self.O_TRUNC = os.O_TRUNC
        self.O_APPEND = os.O_APPEND
        self.O_RDONLY = os.O_RDONLY
    
    def apply_redirections(self, redirections: List[Tuple[str, str]]):
        """Apply a list of redirections to the current process"""
        # First, process and collect all redirections
        saved_fds = {}  # Keep track of saved file descriptors
        
        # Initialize a StateMachineExpander for expanding targets
        expander = StateMachineExpander(os.environ.get, False)
        
        # Process output redirections first, then handle descriptor duplications (2>&1)
        # This ensures that when we redirect stderr to stdout, stdout is already pointing to the right place
        output_redirections = []
        descriptor_redirections = []
        
        # Sort redirections into groups by type
        for op, target in redirections:
            if op == '2>&1':
                descriptor_redirections.append((op, target))
            else:
                output_redirections.append((op, target))
                
        # Process regular file redirections first
        for op, target in output_redirections:
            target = expander.expand_all_with_brace_expansion(target)
                
            # Parse redirection operator for source fd
            if op.startswith('2'):  # stderr redirection
                src_fd = sys.stderr.fileno()
                op = op[1:]  # Remove the '2' prefix
            else:
                src_fd = sys.stdout.fileno() if op.startswith('>') else sys.stdin.fileno()
            
            # Save original fd if not already saved
            if src_fd not in saved_fds:
                saved_fds[src_fd] = os.dup(src_fd)
            
            # Handle different redirection types
            try:
                if op == '>' or op.endswith('>'):
                    # Handle normal file redirection
                    fd = os.open(target, self.O_WRONLY | self.O_CREAT | self.O_TRUNC, 0o644)
                    os.dup2(fd, src_fd)
                    os.close(fd)
                elif op == '>>' or op.endswith('>>'):
                    fd = os.open(target, self.O_WRONLY | self.O_CREAT | self.O_APPEND, 0o644)
                    os.dup2(fd, src_fd)
                    os.close(fd)
                elif op == '<':
                    fd = os.open(target, self.O_RDONLY)
                    os.dup2(fd, src_fd)
                    os.close(fd)
            except Exception as e:
                print(f"Redirection error: {e}", file=sys.stderr)
                os._exit(1)
        
        # Now process descriptor redirections like 2>&1
        # These are processed after regular redirections to ensure stdout is already pointing to the right place
        for op, target in descriptor_redirections:
            if op == '2>&1':
                # Redirect stderr to wherever stdout is currently pointing
                os.dup2(sys.stdout.fileno(), sys.stderr.fileno())


class PipelineExecutor:
    """Handles execution of command pipelines"""
    
    def __init__(self, interactive: bool = True):
        self.interactive = interactive
        self.token_expander = TokenExpander()  # Now instantiates with its own word_expander
        self.redirection_handler = RedirectionHandler()
    
    def create_pipes(self, num_segments: int) -> List[Tuple[int, int]]:
        """Create pipes between commands in a pipeline"""
        pipes = []
        for _ in range(num_segments - 1):
            r, w = os.pipe()
            pipes.append((r, w))
        return pipes
    
    def set_up_child_process(self, pipes: List[Tuple[int, int]], i: int, num_segments: int):
        """Set up pipe redirections for a child process in the pipeline"""
        # Set up pipes
        if i > 0:  # Not first command
            os.dup2(pipes[i-1][0], sys.stdin.fileno())
        if i < num_segments - 1:  # Not last command
            os.dup2(pipes[i][1], sys.stdout.fileno())
        
        # Close all pipe ends after duplication
        for r, w in pipes:
            os.close(r)
            os.close(w)
    
    def execute_child_process(self, cmd: str, args: List[str], 
                              redirections: List[Tuple[str, str]]):
        """Execute a command in a child process"""
        try:
            # Apply redirections
            self.redirection_handler.apply_redirections(redirections)
            
            # Check for shell functions before attempting to execute
            from ..shell import SHELL
            if hasattr(SHELL, '_current_shell') and SHELL._current_shell:
                shell_instance = SHELL._current_shell
                if hasattr(shell_instance, 'ast_executor') and \
                    shell_instance.ast_executor.function_registry.exists(cmd):
                    # This is a shell function - don't try to execute it as an external program
                    print(f"Error: '{cmd}' is a shell function but was attempted to execute as a binary", file=sys.stderr)
                    os._exit(127)  # Command not found exit code
            
            # Process arguments - make sure we don't split quoted arguments with spaces
            processed_args = []
            for i, arg in enumerate(args):
                # Add processed argument
                processed_args.append(arg)
                
                # For debugging
                if os.environ.get('DEBUG_SHELL'):
                    print(f"[SHELL DEBUG] Arg {i}: '{arg}'", file=sys.stderr)
            
            # Execute command
            os.execvp(cmd, processed_args)
        except Exception as e:
            print(f"Failed to execute {cmd}: {e}", file=sys.stderr)
            os._exit(1)
    
    def handle_builtin(self, cmd: str, args: List[str]) -> Optional[int]:
        """Handle builtin commands"""
        if cmd in BUILTINS:
            return BUILTINS[cmd](*args[1:])
        return None
    
    def execute_pipeline(self, tokens: List[Token], background: bool = False) -> Optional[int]:
        """Execute a pipeline of commands"""
        # Split into pipeline segments
        segments = RedirectionParser.split_pipeline(tokens)
        if not segments:
            return 0  # Return 0 instead of None for empty commands
        
        # Create pipes between commands
        pipes = self.create_pipes(len(segments))
        
        # Execute each command in pipeline
        processes = []
        for i, segment in enumerate(segments):
            # Handle redirections
            cmd_tokens, redirections = RedirectionParser.parse_redirections(segment)
            if not cmd_tokens:
                continue
                
            # Debug output for tokens
            if os.environ.get('DEBUG_TOKENS'):
                print("[DEBUG] Raw tokens before expansion:", file=sys.stderr)
                for j, tok in enumerate(cmd_tokens):
                    print(f"  Token {j}: {repr(tok.value)} ({tok.type})", file=sys.stderr)
            
            # Manually handle token expansion with proper quote handling
            expanded_tokens = []
            for token in cmd_tokens:
                # For command substitution, handle normally
                if token.token_type == TokenType.SUBSTITUTION:
                    expanded = expand_command_substitution(token.value)
                    if expanded:
                        expanded_tokens.extend(expanded.split())
                    continue
                    
                # Check if this is a quoted string or has the quoted attribute
                has_quotes = (token.value.startswith('"') and token.value.endswith('"')) or \
                            (token.value.startswith("'") and token.value.endswith("'"))
                was_quoted = hasattr(token, 'quoted') and token.quoted
                
                if has_quotes or was_quoted:
                    # Get the value, stripping quotes if needed
                    if has_quotes:
                        from ..parser.quotes import strip_quotes
                        value = strip_quotes(token.value)
                    else:
                        value = token.value
                    
                    # If it was in double quotes, we still need to expand variables
                    if token.value.startswith('"'):
                        value = expand_variables(value)
                    
                    # Debug output
                    if os.environ.get('DEBUG_TOKENS'):
                        print(f"[TOKEN] Preserving quoted token: '{value}'", file=sys.stderr)
                    
                    # Add as a single token, preserving spaces
                    expanded_tokens.append(value)
                else:
                    # For normal tokens, use standard expansion which may split tokens
                    expanded = expand_all(token.value)
                    
                    # Handle wildcard expansion for unquoted tokens
                    if '*' in expanded or '?' in expanded:
                        import glob
                        matches = glob.glob(expanded)
                        if matches:
                            expanded_tokens.extend(sorted(matches))
                            continue
                            
                    # Handle word splitting
                    if ' ' in expanded:
                        expanded_tokens.extend(expanded.split())
                    else:
                        expanded_tokens.append(expanded)
            
            if not expanded_tokens:
                continue
                
            # Get command and arguments
            cmd = expanded_tokens[0]
            args = expanded_tokens
            
            # Check for variable assignment (VAR=value)
            assignment_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)', cmd)
            if assignment_match and i == 0 and len(segments) == 1 and len(args) == 1:
                var_name = assignment_match.group(1)
                var_value = assignment_match.group(2)
                
                # Strip quotes if present
                if (var_value.startswith('"') and var_value.endswith('"')) or \
                   (var_value.startswith("'") and var_value.endswith("'")):
                    var_value = var_value[1:-1]
                    
                os.environ[var_name] = var_value
                return 0  # Return success for variable assignment
            
            # Check for builtins and functions
            if i == 0 and len(segments) == 1:
                # Check if the command is a shell function
                from ..shell import SHELL
                if hasattr(SHELL, '_current_shell') and SHELL._current_shell:
                    shell_instance = SHELL._current_shell
                    if hasattr(shell_instance, 'ast_executor') and \
                       shell_instance.ast_executor.function_registry.exists(cmd):
                        # This is a function call - use the AST executor to handle it properly
                        from ..parser.ast import CommandNode
                        cmd_node = CommandNode(cmd, args)
                        return shell_instance.ast_executor.visit_command(cmd_node)
                
                # Check for builtin commands
                result = self.handle_builtin(cmd, args)
                if result is not None:
                    return result
            
            # Fork and execute
            pid = os.fork()
            if pid == 0:  # Child
                try:
                    # Set up process group
                    pgid = processes[0] if processes else os.getpid()
                    os.setpgid(0, pgid)
                    
                    if not background and i == 0:
                        TerminalController.set_foreground_pgrp(pgid)
                    
                    # Reset signal handlers to default in child process
                    TerminalController.reset_signal_handlers()
                    
                    # Set up pipes for this process in the pipeline
                    self.set_up_child_process(pipes, i, len(segments))
                    
                    # Execute the command
                    self.execute_child_process(cmd, args, redirections)
                except Exception as e:
                    print(f"Error in child process: {e}", file=sys.stderr)
                    os._exit(1)
            
            processes.append(pid)
        
        # Close all pipe ends in parent after all processes are forked
        for r, w in pipes:
            os.close(r)
            os.close(w)
        
        # If no processes were created, return success
        if not processes:
            return 0
            
        return self.manage_processes(processes, tokens, background)
    
    def manage_processes(self, processes: List[int], tokens: List[Token], 
                         background: bool) -> int:
        """Manage child processes after fork"""
        # Create job if running in background
        if background:
            job = SHELL.add_job(
                command=' '.join(str(t) for t in tokens),
                pgid=processes[0],
                processes=processes
            )
            # Update the $! variable with the PID of the last background process
            SPECIAL_VARS.set_last_bg_pid(processes[0])
            
            print(f"[{job.id}] {processes[0]}")
            return 0  # Return success for background jobs
        
        # Wait for foreground process
        result = self.wait_for_processes(processes, tokens)
        # Ensure we return an int, not None
        return 0 if result is None else result
    
    def wait_for_processes(self, processes: List[int], tokens: List[Token]) -> int:
        """Wait for processes to complete"""
        exit_status = 0  # Default to success
        
        while processes:
            try:
                # Wait for any child process to change state, including stopped processes
                pid, status = os.waitpid(-1, os.WUNTRACED)
                
                if pid in processes:
                    # If child process was stopped (Ctrl-Z)
                    if os.WIFSTOPPED(status):
                        # Create job for stopped process and add the PID that was stopped
                        job = SHELL.add_job(
                            command=' '.join(str(t) for t in tokens),
                            pgid=processes[0],  # Use the process group ID
                            processes=processes.copy(),  # Copy the process list
                            background=True
                        )
                        job.status = JobStatus.STOPPED
                        print(f"\nJob {job.id} stopped")
                        
                        # Break out of the wait loop as the job is now in the background
                        break
                    
                    # Remove the process from our tracking list if it terminated
                    if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                        processes.remove(pid)
                        
                        # Save exit status of last command in pipeline
                        if not processes and os.WIFEXITED(status):
                            exit_status = os.WEXITSTATUS(status)
                        
            except ChildProcessError:
                # No more child processes
                break
                
            except KeyboardInterrupt:
                # Forward interrupt to process group
                try:
                    os.killpg(processes[0], signal.SIGINT)
                except OSError:
                    # Process group may no longer exist
                    pass
        
        # Return terminal to shell
        if self.interactive:
            TerminalController.set_foreground_pgrp(os.getpgrp())
            
        return exit_status