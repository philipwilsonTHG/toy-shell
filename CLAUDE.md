# Python Shell (psh) Development Guidelines

## Build & Test Commands
- Install dev dependencies: `pip install -e ".[dev]"`
- Run all tests: `pytest`
- Run single test file: `pytest tests/test_builtins/test_source.py`
- Run specific test: `pytest tests/test_builtins/test_source.py::test_source_basic_commands -v`
- Run type checking: `mypy src`
- Run linting: `pylint src`
- Start shell: `python3 -m src.shell` or `psh` (if installed)

## Code Style Guidelines
- Use Python type hints throughout the codebase
- Follow PEP 8 naming conventions (snake_case for functions/variables, CamelCase for classes)
- Import organization: standard library → third-party → local modules
- Function return types should be explicitly typed including Optional[T] where applicable
- Handle errors with appropriate exceptions and descriptive error messages
- Document all public functions, classes, and methods with docstrings
- Use f-strings for string formatting
- Avoid globals; use the SHELL context object for state
- Always fix bugs using a new git branch and merge with main after all tests pass
- Increment version number using git tags

## Error Handling
- Use specific exception types where possible
- Always include descriptive error messages in stderr
- Return appropriate exit codes from commands (0 for success, >0 for errors)