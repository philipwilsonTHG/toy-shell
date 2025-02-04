#!/usr/bin/env python3

import os, sys, signal, errno
import re, glob
import readline
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum, auto

version = "psh 0.094"

class JobStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    DONE = auto()

@dataclass
class Job:
    id: int
    pgid: int
    command: str
    status: JobStatus
    processes: List[int]

# Global job control state
jobs: Dict[int, Job] = {}
next_job_id: int = 1

class Command:
    file_redirect_pattern = re.compile(r"(\d*>+$|<)")
    fd_redirect_pattern = re.compile(r"(\d+)>&(\d+)")

    def __init__(self, line):
        self.line = line
        self.stdin = sys.stdin.fileno()
        self.stdout = sys.stdout.fileno()
        self.stderr = sys.stderr.fileno()
        self.line = os.path.expandvars(self.line)
        self.args = lex(self.line)
        self.args = list([os.path.expanduser(token) for token in self.args])
        self.args = glob_args(self.args)
        self.cmd = resolve_path(self.args[0])
        self.apply_redirects()

    def __str__(self):
        return (
            f"{self.args} stdin={self.stdin} stdout={self.stdout} stderr={self.stderr}"
        )

    def apply_redirects(self):
        remove = []
        for index, arg in enumerate(self.args):
            if self.file_redirect_pattern.match(arg):
                self.apply_file_redirect(arg, self.args[index + 1])
                remove.extend((index, index + 1))
            elif match := self.fd_redirect_pattern.match(arg):
                fds = tuple([int(x) for x in match.groups()])
                self.apply_fd_redirect(*fds)
                remove.append(index)
        for index in remove[::-1]:
            del self.args[index]

    def apply_file_redirect(self, verb, filename):
        match verb:
            case ">":
                self.stdout = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            case "<":
                self.stdin = os.open(filename, os.O_RDONLY)
            case ">>":
                self.stdout = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_APPEND)
            case "2>":
                self.stderr = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            case "2>>":
                self.stderr = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_APPEND)

    def apply_fd_redirect(self, from_fd, to_fd):
        if from_fd == 1:
            self.stdout = to_fd
        elif from_fd == 2:
            self.stderr = to_fd
        else:
            print(f"unsupported redirect {from_fd} to {to_fd}")

    def run(self, background=False):
        pid = os.fork()
        if pid == 0:
            # Child process
            try:
                # Create new process group
                pgid = os.getpid()
                os.setpgid(0, pgid)
                
                if not background:
                    # Try to take control of terminal if foreground
                    try:
                        os.tcsetpgrp(sys.stdin.fileno(), pgid)
                    except OSError:
                        pass  # Ignore if we can't set terminal control
                
                # Set up signal handlers
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                signal.signal(signal.SIGTSTP, signal.SIG_DFL)
                signal.signal(signal.SIGTTOU, signal.SIG_DFL)
                
                # Set up I/O
                os.dup2(self.stdin, sys.stdin.fileno())
                os.dup2(self.stdout, sys.stdout.fileno())
                os.dup2(self.stderr, sys.stderr.fileno())
                
                # Execute command
                os.execv(self.cmd, self.args)
            except Exception as e:
                print(f"Failed to execute command: {e}", file=sys.stderr)
                os._exit(1)
        else:
            # Parent process
            try:
                # Put child in its own process group
                pgid = pid  # Use first process as group leader
                os.setpgid(pid, pgid)
                
                # Clean up file descriptors
                self.stdin == sys.stdin.fileno() or os.close(self.stdin)
                self.stdout == sys.stdout.fileno() or self.stdout < 3 or os.close(self.stdout)
                self.stderr == sys.stderr.fileno() or self.stderr < 3 or os.close(self.stderr)
                
                if not background:
                    # Give terminal control to the foreground process group
                    # Wait a moment for child to set up its process group
                    os.tcsetpgrp(sys.stdin.fileno(), pgid)
            except OSError as e:
                # Handle race conditions with child process
                if e.errno != errno.EACCES:
                    raise
            
            return pid, pgid

cwd_history = [os.getcwd()]

def update_job_status():
    """Update status of all jobs"""
    for job in jobs.values():
        if job.status == JobStatus.DONE:
            continue
        
        alive = False
        for pid in job.processes:
            try:
                # Check if process is still running
                os.kill(pid, 0)
                alive = True
                break
            except ProcessLookupError:
                continue
        
        if not alive:
            job.status = JobStatus.DONE

def format_job_status(job: Job) -> str:
    """Format job status for display"""
    status_str = {
        JobStatus.RUNNING: "Running",
        JobStatus.STOPPED: "Stopped",
        JobStatus.DONE: "Done"
    }[job.status]
    
    return f"[{job.id}] {status_str}\t{job.command}"

def jobs_command():
    """shell builtin - list jobs"""
    update_job_status()
    
    # Remove completed jobs
    done_jobs = [jid for jid, job in jobs.items() if job.status == JobStatus.DONE]
    for jid in done_jobs:
        del jobs[jid]
    
    # Display remaining jobs
    for job in sorted(jobs.values(), key=lambda j: j.id):
        print(format_job_status(job))

def bg_command(*args):
    """shell builtin - resume job in background"""
    if not args:
        sys.stderr.write("bg: job id required\n")
        return
    
    try:
        job_id = int(args[0].strip('%'))
    except ValueError:
        sys.stderr.write(f"bg: invalid job id: {args[0]}\n")
        return
    
    if job_id not in jobs:
        sys.stderr.write(f"bg: job {job_id} not found\n")
        return
    
    job = jobs[job_id]
    if job.status == JobStatus.DONE:
        sys.stderr.write(f"bg: job {job_id} has completed\n")
        return
    
    try:
        os.killpg(job.pgid, signal.SIGCONT)
        job.status = JobStatus.RUNNING
        print(format_job_status(job))
    except ProcessLookupError:
        sys.stderr.write(f"bg: job {job_id} not found\n")
        job.status = JobStatus.DONE

def fg_command(*args):
    """shell builtin - bring job to foreground"""
    if not args:
        sys.stderr.write("fg: job id required\n")
        return
    
    try:
        job_id = int(args[0].strip('%'))
    except ValueError:
        sys.stderr.write(f"fg: invalid job id: {args[0]}\n")
        return
    
    if job_id not in jobs:
        sys.stderr.write(f"fg: job {job_id} not found\n")
        return
    
    job = jobs[job_id]
    if job.status == JobStatus.DONE:
        sys.stderr.write(f"fg: job {job_id} has completed\n")
        return
    
    try:
        # Give terminal control to the job
        os.tcsetpgrp(sys.stdin.fileno(), job.pgid)
        
        # Continue the job if it was stopped
        if job.status == JobStatus.STOPPED:
            os.killpg(job.pgid, signal.SIGCONT)
        
        job.status = JobStatus.RUNNING
        
        # Wait for the job to complete or stop
        while job.status == JobStatus.RUNNING:
            try:
                os.waitpid(-job.pgid, os.WUNTRACED)
            except ChildProcessError:
                break
            update_job_status()
        
        # Return terminal control to shell
        os.tcsetpgrp(sys.stdin.fileno(), os.getpgrp())
        
    except ProcessLookupError:
        sys.stderr.write(f"fg: job {job_id} not found\n")
        job.status = JobStatus.DONE

def chdir(newdir=os.path.expanduser("~")):
    """shell builtin - change working directory"""
    newdir = cwd_history[-1] if newdir == "-" else newdir

    try:
        savedir = os.getcwd()
        os.chdir(newdir)
        cwd_history.append(savedir)
    except Exception as e:
        sys.stderr.write(f"cd: {newdir}: {e.strerror}\n")

def exit(status_code="0"):
    """shell builtin - exit()"""
    retcode = int(status_code) & 0xFF if status_code.isnumeric() else 0
    sys.exit(retcode)

def export(*args):
    """shell builtin - set environment variables"""
    if not args:
        # Print all environment variables when no args provided
        for key, value in sorted(os.environ.items()):
            print(f"{key}={value}")
        return

    for arg in args:
        try:
            key, value = arg.split("=", 1)
            if key:
                os.environ[key] = value
        except ValueError:
            sys.stderr.write(f"export: invalid format: {arg}\n")

def unset(*args):
    """shell builtin - unset environment variables"""
    if not args:
        sys.stderr.write("unset: missing variable name\n")
        return
    
    for arg in args:
        try:
            del os.environ[arg]
        except KeyError:
            sys.stderr.write(f"unset: {arg}: not found\n")

def source(*args):
    """shell builtin - execute commands from a file"""
    if not args:
        sys.stderr.write("source: filename argument required\n")
        return
    
    filename = os.path.expanduser(args[0])
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    try:
                        process_line(line)
                    except Exception as e:
                        sys.stderr.write(f"source: error executing '{line}': {e}\n")
    except FileNotFoundError:
        sys.stderr.write(f"source: {filename}: No such file\n")
    except PermissionError:
        sys.stderr.write(f"source: {filename}: Permission denied\n")
    except Exception as e:
        sys.stderr.write(f"source: error reading {filename}: {e}\n")

builtins = {
    "cd": chdir,
    "exit": exit,
    "version": lambda: print(version),
    "export": export,
    "unset": unset,
    "jobs": jobs_command,
    "bg": bg_command,
    "fg": fg_command,
    "source": source,
    ".": source  # Add dot command as alias for source
}

def pipesplit(line):
    """Split a command line into pipeline segments, respecting quotes"""
    segments = []
    current = []
    in_single_quote = False
    in_double_quote = False
    escaped = False
    
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
        elif char == '|' and not in_single_quote and not in_double_quote:
            segments.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    
    if current:
        segments.append(''.join(current).strip())
    
    return segments

def tokenize(line):
    """Tokenize a command line into arguments, handling quotes and escapes"""
    tokens = []
    current = []
    in_single_quote = False
    in_double_quote = False
    escaped = False
    
    for char in line:
        if escaped:
            if char in '"\'\\$':  # Only escape special characters
                current.append(char)
            else:
                current.extend(['\\', char])
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char.isspace() and not in_single_quote and not in_double_quote:
            if current:
                tokens.append(''.join(current))
                current = []
        else:
            current.append(char)
    
    if escaped:
        current.append('\\')
    if current:
        tokens.append(''.join(current))
    
    # Remove surrounding quotes if present
    tokens = [remove_quotes(token) for token in tokens]
    return tokens

def remove_quotes(token):
    """Remove surrounding quotes from a token if present"""
    if len(token) >= 2:
        if (token[0] == '"' and token[-1] == '"') or (token[0] == "'" and token[-1] == "'"):
            return token[1:-1]
    return token

def execute_command_substitution(command):
    """Execute a command and return its output as a string"""
    # Remove the $() wrapper
    command = command[2:-1].strip()
    
    # Create temporary files for output capture
    with tempfile.TemporaryFile() as stdout_file:
        try:
            # Execute command and capture output
            subprocess.run(command, shell=True, stdout=stdout_file, stderr=subprocess.PIPE, text=True)
            stdout_file.seek(0)
            output = stdout_file.read().decode().strip()
            return output
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"Command substitution failed: {e}\n")
            return ""

def expand_command_substitution(line):
    """Expand $(command) syntax in the input line"""
    pattern = r'\$\([^()]+\)'
    while re.search(pattern, line):
        match = re.search(pattern, line)
        if match:
            cmd = match.group(0)
            output = execute_command_substitution(cmd)
            line = line[:match.start()] + output + line[match.end():]
    return line

def lex(line):
    """Tokenize input line with proper quote and escape handling"""
    # First expand command substitutions
    line = expand_command_substitution(line.strip())
    # Then tokenize with quote and escape handling
    return tokenize(line)

def glob_args(arglist):
    globbed = (glob.glob(token) or [token] for token in arglist)
    return list([token for sublist in globbed for token in sublist])

def resolve_path(progname):
    if progname[0] == "." and os.path.isfile(progname):
        return progname

    for directory in os.environ["PATH"].split(":"):
        testpath = os.path.join(directory, progname)
        if os.path.isfile(testpath):
            return testpath
    return None

def prompt():
    home = os.path.expanduser("~")
    path = os.getcwd().replace(home, "~")
    return f"{os.getlogin()}@{os.uname().nodename}:{path}$ "

def add_pipe_descriptors(commands):
    i = 0
    while i <= len(commands) - 2:
        commands[i + 1].stdin, commands[i].stdout = os.pipe()
        i += 1

def process_line(line):
    global next_job_id
    
    sig, ret = 0, 0
    background = line.endswith('&')
    if background:
        line = line[:-1].strip()

    tokens = lex(line)
    if not tokens:
        return
        
    first_token = tokens[0]

    if first_token in builtins:
        tokens = [os.path.expanduser(token) for token in tokens]
        tokens = glob_args(tokens)
        return builtins[first_token](*tokens[1:])

    commands = [Command(str) for str in pipesplit(line)]
    add_pipe_descriptors(commands)

    # Create new job
    job = Job(
        id=next_job_id,
        pgid=0,  # Will be set after first process starts
        command=line,
        status=JobStatus.RUNNING,
        processes=[]
    )
    next_job_id += 1

    for command in commands:
        pid, pgid = command.run(background)
        if job.pgid == 0:
            job.pgid = pgid
        job.processes.append(pid)

    if background:
        jobs[job.id] = job
        print(f"[{job.id}] {job.pgid}")
    else:
        # Wait for foreground job
        while True:
            try:
                pid, status = os.waitpid(-job.pgid, os.WUNTRACED)
                if os.WIFSTOPPED(status):
                    job.status = JobStatus.STOPPED
                    jobs[job.id] = job
                    print(f"\nJob {job.id} stopped")
                    break
                elif os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    if pid == job.processes[-1]:  # Last process in pipeline
                        break
            except ChildProcessError:
                break
            except KeyboardInterrupt:
                os.killpg(job.pgid, signal.SIGINT)
                break
        
        # Return terminal control to shell
        os.tcsetpgrp(sys.stdin.fileno(), os.getpgrp())

def main():
    while True:
        try:
            line = input(prompt()).strip()
            if not line:
                continue

            result = re.search(r"^\s*(eval|exec)\s*(.*)", line)
            if result and len(result.groups()) == 2:
                (verb, arg) = result.groups()
                if verb == "eval":
                    print(eval(arg))
                elif verb == "exec":
                    exec(arg.lstrip())
                continue
            else:
                process_line(line)
        except KeyboardInterrupt:
            print()
            continue

def init_readline():
    readline.parse_and_bind("tab: complete")
    histfile = os.path.join(os.path.expanduser("~"), ".python_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except FileNotFoundError:
        pass

def run_script(filename):
    """Run commands from a script file"""
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    try:
                        process_line(line)
                    except Exception as e:
                        sys.stderr.write(f"Error executing '{line}': {e}\n")
                        return 1
        return 0
    except FileNotFoundError:
        sys.stderr.write(f"Error: {filename}: No such file\n")
        return 1
    except PermissionError:
        sys.stderr.write(f"Error: {filename}: Permission denied\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Error reading {filename}: {e}\n")
        return 1

if __name__ == "__main__":
    # Put shell in its own process group and take control of the terminal
    os.setpgrp()
    os.tcsetpgrp(sys.stdin.fileno(), os.getpgrp())
    
    # Set up signal handlers
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)
    signal.signal(signal.SIGTTIN, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Check for script file argument
    if len(sys.argv) > 1:
        script_file = sys.argv[1]
        sys.exit(run_script(script_file))
    
    # No script file, run interactive shell
    init_readline()
    try:
        main()
    except EOFError:
        print()
        sys.exit(0)
