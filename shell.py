#!/usr/bin/env python3

import os, sys, signal
import re, glob
import readline

version = 'psh 0.09'

class Command():
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
        return f'{self.args} stdin={self.stdin} stdout={self.stdout} stderr={self.stderr}'
        
    def apply_redirects(self):
        remove = []
        for index, arg in enumerate(self.args):
            if self.file_redirect_pattern.match(arg):
                self.apply_file_redirect(arg, self.args[index + 1])
                remove.extend((index, index+1))
            elif match := self.fd_redirect_pattern.match(arg):
                fds = tuple([int(x) for x in match.groups()])
                self.apply_fd_redirect(*fds)
                remove.append(index)
        for index in remove[::-1]:
            del(self.args[index])

    def apply_file_redirect(self, verb, filename):
        match verb:
            case '<':
                self.stdin = os.open(filename, os.O_RDONLY)
            case '>':
                self.stdout = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            case '>>':
                self.stdout = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_APPEND)
            case '2>':
                self.stderr = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            case '2>>':
                self.stderr = os.open(filename, os.O_CREAT | os.O_WRONLY | os.O_APPEND)

    def apply_fd_redirect(self, from_fd, to_fd):
        if from_fd == 1:
            self.stdout = to_fd
        elif from_fd == 2:
            self.stderr = to_fd
        else:
            print(f"unsupported redirect {from_fd} to {to_fd}") 
                
    def run(self):
        cmd = self.args[0]
        if cmd in builtins:
            return builtins[cmd](*self.args[1:])
        
        pid = os.fork()
        if pid == 0:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            os.dup2(self.stdin, sys.stdin.fileno())
            os.dup2(self.stdout, sys.stdout.fileno())
            os.dup2(self.stderr, sys.stderr.fileno())
            os.execv(self.cmd, self.args)        
        else:
            self.stdin == sys.stdin.fileno() or  os.close(self.stdin)
            self.stdout == sys.stdout.fileno() or self.stdout < 3 or os.close(self.stdout)
            self.stderr == sys.stderr.fileno() or self.stderr < 3 or os.close(self.stderr)
        return pid

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

builtins = {'cd' : chdir, 'exit': exit, 'version': lambda: print(version) }

def pipesplit(str):
    return str.split('|')

def lex(line):
    return line.strip().split()

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

def add_pipe_descriptors(commands):
    i = 0
    while i <= len(commands) - 2:
        commands[i+1].stdin, commands[i].stdout = os.pipe()
        i += 1

def process_line(line):
    commands = pipesplit(line)
    commands = [Command(str) for str in commands]
    add_pipe_descriptors(commands)

    childprocs = []
    for command in commands:
        pid = command.run()
        if pid:
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

        result = re.search(r"^\s*(eval|exec)\s*(.*)", line)
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
