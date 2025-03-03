#!/usr/bin/env python3

import sys
from typing import List

def eval_expr(*args: str) -> int:
    """Evaluate Python expressions
    
    Usage:
        eval expression
    """
    if not args:
        return 0
    
    # Join arguments into expression string
    expr = ' '.join(args)
    
    try:
        # Evaluate Python expression using built-in eval
        result = eval(expr, {}, {})
        if result is not None:
            print(result)
        return 0
    except Exception as e:
        print(f"eval: {e}", file=sys.stderr)
        return 1
