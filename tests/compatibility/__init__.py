"""
Compatibility testing framework for comparing psh and bash behaviors.
"""

from .framework import (
    ShellCompatibilityTester,
    CommandResult,
    create_compatibility_test,
    create_multi_command_test
)

__all__ = [
    'ShellCompatibilityTester',
    'CommandResult',
    'create_compatibility_test',
    'create_multi_command_test'
]