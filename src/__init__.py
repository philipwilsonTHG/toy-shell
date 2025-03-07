"""
Toy Shell - A Python-based Unix shell implementation
"""

try:
    from ._version import version as __version__
except ImportError:
    # Fallback version when not installed from git (e.g., source release)
    __version__ = "0.3.0+unknown"
