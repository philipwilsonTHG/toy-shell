#!/usr/bin/env python3

import os
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import patch, MagicMock
from io import StringIO

from src.parser.lexer import Token, tokenize
from src.execution.pipeline import PipelineExecutor, RedirectionHandler

class RedirectionTests(unittest.TestCase):
    """Tests for file redirection functionality"""
    
    def setUp(self):
        """Set up the test environment"""
        self.pipeline_executor = PipelineExecutor(interactive=False)
        self.redirection_handler = RedirectionHandler()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.temp_dir.name, "test_file.txt")
        
    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()
        
    def test_stdout_redirection(self):
        """Test redirecting stdout to a file"""
        with open(self.test_file, 'w') as f:
            f.write("")
            
        # Apply stdout redirection
        with patch('sys.stdout', new=StringIO()):
            redirections = [(">", self.test_file)]
            self.redirection_handler.apply_redirections(redirections)
            
            # Write to stdout
            print("Test output to file")
            sys.stdout.flush()
            
        # Check if the file contains the output
        with open(self.test_file, 'r') as f:
            content = f.read().strip()
            self.assertEqual(content, "Test output to file")
            
    def test_stderr_redirection(self):
        """Test redirecting stderr to a file"""
        with open(self.test_file, 'w') as f:
            f.write("")
            
        # Apply stderr redirection
        with patch('sys.stderr', new=StringIO()):
            redirections = [("2>", self.test_file)]
            self.redirection_handler.apply_redirections(redirections)
            
            # Write to stderr
            print("Test error output to file", file=sys.stderr)
            sys.stderr.flush()
            
        # Check if the file contains the error output
        with open(self.test_file, 'r') as f:
            content = f.read().strip()
            self.assertEqual(content, "Test error output to file")
            
    def test_stderr_to_stdout_redirection(self):
        """Test redirecting stderr to stdout (2>&1)"""
        # Create a temporary file for stdout
        stdout_file = os.path.join(self.temp_dir.name, "stdout.txt")
        
        # Set up redirections
        redirections = [(">", stdout_file), ("2>&1", "1")]
        
        # Use the redirection handler to apply redirections
        # This is challenging to mock in Python's unittest because of file descriptor manipulation
        # So we'll run a separate process to verify this
        test_script = f"""
        import os
        import sys
        from src.execution.pipeline import RedirectionHandler
        
        # Apply redirections
        handler = RedirectionHandler()
        handler.apply_redirections({redirections})
        
        # Write to stdout and stderr
        print("Stdout text")
        print("Stderr text", file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        """
        
        test_file = os.path.join(self.temp_dir.name, "test_script.py")
        with open(test_file, 'w') as f:
            f.write(test_script)
            
        # Run the script to test redirections
        subprocess.run([sys.executable, test_file], check=True)
        
        # Check the content of the stdout file
        with open(stdout_file, 'r') as f:
            content = f.read()
            self.assertIn("Stdout text", content)
            self.assertIn("Stderr text", content)
            
    def test_2_gt_1_redirection_with_pipeline(self):
        """Test 2>&1 redirection with the pipeline executor"""
        # Create a command that writes to both stdout and stderr
        test_script = f"""
        import sys
        print("Stdout message")
        print("Stderr message", file=sys.stderr)
        """
        
        test_file = os.path.join(self.temp_dir.name, "test_script.py")
        with open(test_file, 'w') as f:
            f.write(test_script)
            
        output_file = os.path.join(self.temp_dir.name, "output.txt")
            
        # Create the command tokens
        cmd = f"{sys.executable} {test_file} > {output_file} 2>&1"
        tokens = tokenize(cmd)
        
        # Execute through the pipeline
        self.pipeline_executor.execute_pipeline(tokens)
        
        # Check the content of the output file
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("Stdout message", content)
            self.assertIn("Stderr message", content)
            
if __name__ == '__main__':
    unittest.main()