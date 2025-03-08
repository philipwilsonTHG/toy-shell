#!/usr/bin/env python3
# This is a standalone script, not a pytest test file

import time
import sys
from src.parser.state_machine_adapter import StateMachineWordExpander

# Simple performance test comparing both expanders

# Test data
SIMPLE_VAR = "$name"
COMPLEX_VAR = "${name:-default}"
ARITHMETIC = "$((1 + 2 * (3 + 4)))"
MIXED = "Hello $name, today is $(date) and $((1+2)) equals 3"

# Number of iterations
ITERATIONS = 10000

def test_variable_provider(var_name):
    # Simple variable provider
    variables = {
        "name": "World",
        "path": "/usr/local/bin",
        "count": "42"
    }
    return variables.get(var_name)

def run_test(expander_class, name):
    expander = expander_class(test_variable_provider, debug_mode=False)
    
    start_time = time.time()
    
    # Run the tests
    for _ in range(ITERATIONS):
        expander.expand(SIMPLE_VAR)
        expander.expand(COMPLEX_VAR)
        expander.expand(ARITHMETIC)
        expander.expand(MIXED)
        
    end_time = time.time()
    elapsed = end_time - start_time
    
    return elapsed

# Run tests with the state machine expander
print(f"Running {ITERATIONS} iterations of each expansion test...")

# Test with state machine expander
sm_time = run_test(StateMachineWordExpander, "State Machine Expander")
print(f"State Machine Expander: {sm_time:.4f}s")