#!/usr/bin/env python3
"""
Compatibility tests for find and xargs commands.

These tests verify that psh processes pipes, find, and xargs commands the same
way as bash would.
"""

import os
import tempfile
import shutil
import pytest
from .framework import ShellCompatibilityTester


class TestFindXargs:
    """Test find and xargs command compatibility between psh and bash."""
    
    def setup_method(self):
        self.tester = ShellCompatibilityTester()
        # Create a temporary test directory
        self.test_dir = tempfile.mkdtemp(prefix="psh_find_test_")
        
        # Create a set of test files
        self.create_test_files()
        
    def teardown_method(self):
        # Clean up the test directory
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """Create a set of test files for find command testing."""
        # Create Python files with specific number of lines
        files = {
            "main.py": ["# Main file", "print('Hello, world!')", "# End"],
            "utils.py": ["# Utils module", "def helper():", "    return True"],
            "test.py": ["# Test file", "assert True"],
            "data.txt": ["This is a text file", "Not a Python file"],
            "empty.py": []
        }
        
        for filename, content in files.items():
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                f.write('\n'.join(content))
    
    def test_find_name_filter(self):
        """Test basic find command with name filter."""
        # The -name option is in quotes, so it should be treated as a pattern
        cmd = f"cd {self.test_dir} && find . -name '*.py' | sort"
        self.tester.assert_outputs_match(cmd)
    
    def test_find_pipe_to_wc(self):
        """Test find piped to wc to count files."""
        cmd = f"cd {self.test_dir} && find . -name '*.py' | wc -l"
        self.tester.assert_outputs_match(cmd)
    
    def test_find_with_xargs(self):
        """Test find with xargs to count lines in Python files."""
        # Note: we use -print0 and -0 for filenames with spaces
        cmd = f"cd {self.test_dir} && find . -name '*.py' -print0 | xargs -0 wc -l | sort"
        self.tester.assert_outputs_match(cmd, normalize_whitespace=True)
    
    def test_find_exec(self):
        """Test find with -exec option."""
        cmd = f"cd {self.test_dir} && find . -name '*.py' -exec echo 'Found:' {{}} \\;"
        self.tester.assert_outputs_match(cmd)
    
    def test_complex_find_pipe(self):
        """Test a more complex find command with grep and sed."""
        cmd = f"""
        cd {self.test_dir} && find . -name '*.py' | grep -v 'empty' | 
        xargs grep -l 'print\\|def' 2>/dev/null || echo 'No matches'
        """
        self.tester.assert_outputs_match(cmd, normalize_whitespace=True)
        
    def test_find_print_xargs(self):
        """Test the specific case: find . -print "*py" | xargs wc -l."""
        # Create test data with different file patterns
        # Note: -print "*py" in the example doesn't actually work correctly in bash
        # The correct syntax is either -name "*.py" or just *.py with proper quoting
        pyfiles = ["testfile1.py", "testfile2.py", "otherfile.txt"]
        for f in pyfiles:
            with open(os.path.join(self.test_dir, f), 'w') as file:
                file.write("line 1\nline 2\n")
                
        # Test the requested command (with correct syntax)
        cmd = f"cd {self.test_dir} && find . -name '*.py' | xargs wc -l"
        self.tester.assert_outputs_match(cmd, normalize_whitespace=True)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])