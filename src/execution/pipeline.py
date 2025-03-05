#!/usr/bin/env python3

import os
import sys
import signal
from typing import List, Tuple, Dict, Optional

from ..parser.lexer import Token, parse_redirections, split_pipeline
from ..parser.expander import expand_all, expand_command_substitution
from ..context import SHELL, JobStatus
from ..utils.terminal import TerminalController
from ..builtins import BUILTINS


class TokenExpander:
    """Handles expansion of tokens (variables, wildcards, etc.)"""
    
    @staticmethod
    def expand_token(token: Token) -> List[str]:
        """Expand a single token into a list of strings"""
        expanded_tokens = []
        
        if token.type == 'substitution':
            # Handle command substitution
            expanded = expand_command_substitution(token.value)
            if expanded:
                expanded_tokens.extend(expanded.split())
        else:
            # Check if the token is quoted first before any other expansion
            is_double_quoted = token.value.startswith('"') and token.value.endswith('"')
            is_single_quoted = token.value.startswith("'") and token.value.endswith("'")
            
            # Handle other expansions including variables
            expanded = expand_all(token.value)
            
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
    
    @staticmethod
    def expand_tokens(tokens: List[Token]) -> List[str]:
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
                expanded_tokens.extend(TokenExpander.expand_token(token))
                
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
        for op, target in redirections:
            target = expand_all(target)
            
            # Parse redirection operator for source fd
            if op.startswith('2'):  # stderr redirection
                src_fd = sys.stderr.fileno()
                op = op[1:]  # Remove the '2' prefix
            else:
                src_fd = sys.stdout.fileno() if op.startswith('>') else sys.stdin.fileno()
            
            # Handle different redirection types
            if op == '>' or op.endswith('>'):
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


class PipelineExecutor:
    """Handles execution of command pipelines"""
    
    def __init__(self, interactive: bool = True):
        self.interactive = interactive
        self.token_expander = TokenExpander()
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
        segments = split_pipeline(tokens)
        if not segments:
            return 0  # Return 0 instead of None for empty commands
        
        # Create pipes between commands
        pipes = self.create_pipes(len(segments))
        
        # Execute each command in pipeline
        processes = []
        for i, segment in enumerate(segments):
            # Handle redirections
            cmd_tokens, redirections = parse_redirections(segment)
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
                if token.type == 'substitution':
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
                        from ..parser.expander import expand_variables
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
            
            # Check for builtin (but only for simple commands, not in pipelines)
            if i == 0 and len(segments) == 1:
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