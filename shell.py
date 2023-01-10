#!/usr/bin/env python3

import os, sys, signal
import re, glob
import readline
from dataclasses import dataclass

@dataclass
class Command():
    cmd: str
    args: list
    stdin: int = 0
    stdout: int = 1
    stderr: int = 2

cwd_history = [os.getcwd()]

def chdir(newdir = os.path.expanduser('~')):
    ''' shell builtin - change working directory '''
    newdir = cwd_history[-1] if newdir == '-' else newdir
    
    try:
        savedir = os.getcwd()
        os.chdir(newdir)
        cwd_history.append(savedir)
    except Exception as e:
        sys.stderr.write(f'cd: {newdir}: {e.strerror}\n')

def exit(status_code = '0'):
    ''' shell builtin - exit() '''
    retcode = int(status_code) & 0xff if status_code.isnumeric() else 0
    sys.exit(retcode)

builtins = {'cd' : chdir, 'exit': exit}

def pipesplit(str):
    return str.split('|')

def lex(text):
    return text.strip().split()

def expand_user(arglist):
    return list([os.path.expanduser(token) for token in arglist])

def glob_args(arglist):
    globbed = (glob.glob(token) or [token] for token in arglist)
    return list([token for sublist in globbed for token in sublist])

def resolve_path(progname):
    if progname[0] == '.' and os.path.isfile(progname):
        return progname

    for directory in os.environ["PATH"].split(':'):
        testpath = os.path.join(directory, progname)
        if os.path.isfile(testpath):
            return testpath
    return None

def prompt():
    home = os.path.expanduser("~")
    path = os.getcwd().replace(home, "~")
    return f'{os.getlogin()}@{os.uname().nodename}:{path}$ '

def run_command(cmd):
    pid = os.fork()
    if pid == 0:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        os.dup2(cmd.stdin, 0)
        os.dup2(cmd.stdout, 1)
        os.dup2(cmd.stderr, 2)
        os.execv(cmd.cmd, cmd.args)        
    else:
        if cmd.stdin != 0:
            os.close(cmd.stdin)
        if cmd.stdout != 1:
            os.close(cmd.stdout)
        if cmd.stderr != 2:
            os.close(cmd.stderr)
            
    return pid

def process_line(line):
    sig, ret = 0, 0
        
    tokens = [os.path.expanduser(token) for token in lex(line)]
    tokens = glob_args(tokens)
    cmd = tokens[0]
        
    if cmd in builtins:
        return builtins[cmd](*tokens[1:])
    
    commands = pipesplit(line)
    commands = [lex(str) for str in commands]
    commands = [expand_user(x) for x in commands]
    commands = [glob_args(cmd) for cmd in commands]
    commands = list([Command(resolve_path(cmd[0]), cmd) for cmd in commands])
    
    if len(commands) > 1:
        i = 0
        while i <= len(commands) - 2:
            commands[i+1].stdin, commands[i].stdout = os.pipe2(0)
            i += 1

    childprocs = []
    for command in commands:
        pid = run_command(command)
        childprocs.append(pid)

        while childprocs:
            (childpid, status) = os.wait()
            childprocs.remove(childpid)
            sig, ret = status & 0xff, (status & 0xff00) >> 8
            if sig:
                core, signum = sig & 0x80, sig & 0x7f
                print(f'{signal.Signals(signum).name}', 'core dumped' if core else '')

def main():
    while True:
        line = input(prompt()).strip()
        if not line:
            continue

        result = re.search(r"(eval|exec)\((.*)\)", line)
        if result and len(result.groups()) == 2:
            (verb, arg) = result.groups()
            if verb == 'eval':
                print(eval(arg))
            elif verb == 'exec':
                exec(arg.lstrip())
            continue
        else:
            process_line(line)

        
def init_readline():
    readline.parse_and_bind("tab: complete")
    histfile = os.path.join(os.path.expanduser("~"), ".python_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
        
    except FileNotFoundError:
        pass

if __name__ == '__main__':
    init_readline()
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        main()
        
    except EOFError:
        print()
        sys.exit(0)
