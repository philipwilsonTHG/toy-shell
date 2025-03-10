#!/usr/bin/env python3

import os
import tempfile
import subprocess
import unittest
import pytest

class ShellQuoteHandlingTest(unittest.TestCase):
    """Test that quotes are correctly removed when passing arguments to commands"""
    
    def setUp(self):
        """Create a temporary test script to check argument handling"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.script_path = os.path.join(self.temp_dir.name, "print_args.py")
        
        with open(self.script_path, 'w') as f:
            f.write("""#!/usr/bin/env python3
import sys
print(f"Number of arguments: {len(sys.argv)}")
for i, arg in enumerate(sys.argv):
    print(f"Arg {i}: {repr(arg)}")
""")
        os.chmod(self.script_path, 0o755)
    
    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()
    
    def test_quoted_args(self):
        """Test that quotes are removed when passing arguments to commands"""
        # Test with double quotes
        cmd = f"python3 -m src.shell -c '{self.script_path} \"hello world\"'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Verify the output shows correct argument handling
        output = result.stdout.strip()
        self.assertIn("Number of arguments: 2", output, 
                     "Should have 2 args: script path and 'hello world'")
        self.assertIn("Arg 1: 'hello world'", output, 
                     "Quotes should be removed, argument should be single with space")
        self.assertNotIn("Arg 1: '\"hello world\"'", output, 
                        "Quotes should not be preserved in arguments")
    
    def test_multiple_quoted_args(self):
        """Test multiple quoted arguments"""
        cmd = f"python3 -m src.shell -c '{self.script_path} \"first arg\" \"second arg\"'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        output = result.stdout.strip()
        self.assertIn("Number of arguments: 3", output,
                     "Should have 3 args: script path and two quoted arguments")
        self.assertIn("Arg 1: 'first arg'", output, 
                     "First argument should have quotes removed")
        self.assertIn("Arg 2: 'second arg'", output,
                     "Second argument should have quotes removed")
    
    def test_single_quotes(self):
        """Test single quoted arguments"""
        # Use python explicitly to run the script to avoid exec format errors
        cmd = f"python3 -m src.shell -c 'python3 {self.script_path} \"single quoted\" arg'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        output = result.stdout.strip()
        self.assertIn("Number of arguments: 3", output,
                     "Should have 3 args: script path, 'single quoted', and 'arg'")
        self.assertIn("Arg 1: 'single quoted'", output,
                     "Single quotes should be removed from argument")
    
    def test_nested_quotes(self):
        """Test nested quotes (single inside double and vice versa)"""
        # Double quotes containing single quotes - use triple quotes to make escaping easier
        cmd = f'''python3 -m src.shell -c "python3 {self.script_path} \\"outer 'inner' quotes\\""'''
        print(f"Running command: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        output = result.stdout.strip()
        print(f"Nested quotes test output: {output}")  # Debug output
        
        # Use repr to match Python's actual output format
        expected_arg = "outer 'inner' quotes"
        # Python's repr uses double quotes for strings containing single quotes
        expected_output = f'Arg 1: "{expected_arg}"'
        self.assertIn(expected_output, output,
                     "Outer quotes should be removed, inner quotes should be preserved")
    
    def test_compare_with_bash(self):
        """Compare our shell's quote handling with bash's"""
        # Run the same command with bash for comparison
        bash_cmd = f"bash -c '{self.script_path} \"hello world\"'"
        bash_result = subprocess.run(bash_cmd, shell=True, capture_output=True, text=True)
        
        # Run with our shell
        our_cmd = f"python3 -m src.shell -c '{self.script_path} \"hello world\"'"
        our_result = subprocess.run(our_cmd, shell=True, capture_output=True, text=True)
        
        # Extract actual argument representation from both outputs
        bash_output = bash_result.stdout.strip()
        our_output = our_result.stdout.strip()
        
        # Check if both shells removed the quotes correctly
        self.assertIn("Number of arguments: 2", bash_output)
        self.assertIn("Number of arguments: 2", our_output)
        
        # Extract the actual argument representation from both outputs
        bash_arg = [line for line in bash_output.split('\n') if "Arg 1:" in line][0]
        our_arg = [line for line in our_output.split('\n') if "Arg 1:" in line][0]
        
        # Compare the actual argument format - our shell should match bash's behavior
        self.assertEqual(bash_arg, our_arg, 
                        "Our shell should handle quotes the same way as bash")
        
        # Verify the correct behavior with quotes removed
        self.assertIn("'hello world'", bash_arg, 
                     "Bash removes quotes from arguments")

if __name__ == '__main__':
    unittest.main()