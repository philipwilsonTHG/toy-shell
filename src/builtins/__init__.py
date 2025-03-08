"""
Built-in shell commands
"""

from typing import Dict, Callable, Any
from .core import cd, exit_shell, version, source, function_command
from .env import export, unset
from .jobs import jobs, bg, fg
from .history import history
from .eval import eval_expr
from .test import test_command

# Map of builtin command names to their implementations
BUILTINS: Dict[str, Callable[..., Any]] = {
    "cd": cd,
    "exit": exit_shell,
    "version": version,
    "export": export,
    "unset": unset,
    "jobs": jobs,
    "bg": bg,
    "fg": fg,
    "history": history,
    "eval": eval_expr,
    ".": source,
    "source": source,
    "test": test_command,
    "[": test_command,
    "function": function_command
}
