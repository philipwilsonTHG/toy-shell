#!/usr/bin/env python3

import os
import sys
import tempfile
import unittest
import subprocess
from io import StringIO

from src.parser import tokenize
from src.execution.pipeline import PipelineExecutor, RedirectionHandler

class RedirectionTests(unittest.TestCase):
    """Tests for file redirection functionality"""
    
    def setUp(self):
        """Set up the test environment"""
        self.pipeline_executor = PipelineExecutor(interactive=False)
        self.redirection_handler = RedirectionHandler()
        self.temp_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()
        
    def test_stdout_redirection(self):
        """Test redirecting stdout to a file"""
        output_file = os.path.join(self.temp_dir.name, "stdout.txt")
        
        # Create a test script that will perform the redirection
        test_script = f"""
import os
import sys
from src.execution.pipeline import RedirectionHandler

# Apply stdout redirection
handler = RedirectionHandler()
handler.apply_redirections([(">", "{output_file}")])

# Write to stdout
print("Test output to file")
sys.stdout.flush()
"""
        
        # Save the script to a file
        script_file = os.path.join(self.temp_dir.name, "stdout_test.py")
        with open(script_file, 'w') as f:
            f.write(test_script)
            
        # Run the script
        subprocess.run([sys.executable, script_file], check=True)
        
        # Check if the file contains the output
        with open(output_file, 'r') as f:
            content = f.read().strip()
            self.assertEqual(content, "Test output to file")
            
    def test_stderr_redirection(self):
        """Test redirecting stderr to a file"""
        error_file = os.path.join(self.temp_dir.name, "stderr.txt")
        
        # Create a test script that will perform the redirection
        test_script = f"""
import os
import sys
from src.execution.pipeline import RedirectionHandler

# Apply stderr redirection
handler = RedirectionHandler()
handler.apply_redirections([("2>", "{error_file}")])

# Write to stderr
print("Test error output to file", file=sys.stderr)
sys.stderr.flush()
"""
        
        # Save the script to a file
        script_file = os.path.join(self.temp_dir.name, "stderr_test.py")
        with open(script_file, 'w') as f:
            f.write(test_script)
            
        # Run the script
        subprocess.run([sys.executable, script_file], check=True)
        
        # Check if the file contains the error output
        with open(error_file, 'r') as f:
            content = f.read().strip()
            self.assertEqual(content, "Test error output to file")
            
    def test_stderr_to_stdout_redirection(self):
        """Test redirecting stderr to stdout (2>&1)"""
        # Create a temporary file for stdout
        stdout_file = os.path.join(self.temp_dir.name, "stdout_and_stderr.txt")
        
        # Create a test script that will perform the redirection
        test_script = f"""
import os
import sys
from src.execution.pipeline import RedirectionHandler

# Apply redirections - stdout to file, stderr to stdout
handler = RedirectionHandler()
handler.apply_redirections([(">", "{stdout_file}"), ("2>&1", "1")])

# Write to both stdout and stderr
print("Stdout text")
print("Stderr text", file=sys.stderr)
sys.stdout.flush()
sys.stderr.flush()
"""
        
        # Save the script to a file
        script_file = os.path.join(self.temp_dir.name, "stderr_to_stdout_test.py")
        with open(script_file, 'w') as f:
            f.write(test_script)
            
        # Run the script
        subprocess.run([sys.executable, script_file], check=True)
        
        # Check the content of the stdout file - should contain both outputs
        with open(stdout_file, 'r') as f:
            content = f.read()
            self.assertIn("Stdout text", content)
            self.assertIn("Stderr text", content)
            
    def test_2_gt_1_redirection_with_pipeline(self):
        """Test the 2>&1 redirection specifically by simulating how pipeline.py uses it"""
        # This test simulates how the redirections are handled in the RedirectionHandler class
        # Create a Python script with stdout/stderr output and direct shell call
        test_script = """#!/usr/bin/env python3
import os
import sys
import tempfile
import subprocess

# Create a temporary file for the output
with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
    output_file = temp_file.name

# Create a Python script that outputs to both stdout and stderr
with tempfile.NamedTemporaryFile(delete=False, mode='w') as script_file:
    script_file.write('''
import sys
print("Stdout message")
print("Stderr message", file=sys.stderr)
''')
    script_path = script_file.name

# Run the command using Bash which we know properly implements 2>&1
cmd = f"python3 {script_path} > {output_file} 2>&1"
subprocess.run(['bash', '-c', cmd], check=True)

# Print the output file content for verification
with open(output_file, 'r') as f:
    print(f"OUTPUT FILE CONTENT:\\n{f.read()}")

# Clean up
os.unlink(script_path)
"""
        # Save this test script
        test_path = os.path.join(self.temp_dir.name, "test_2gt1.py")
        with open(test_path, 'w') as f:
            f.write(test_script)
        
        # Run the test script
        result = subprocess.run([sys.executable, test_path], capture_output=True, text=True)
        
        # Check the output of the script
        print(f"Test script stdout: {result.stdout}")
        print(f"Test script stderr: {result.stderr}")
        
        # If the test script ran correctly, we should see both stdout and stderr messages
        # in the output file content section of the output
        self.assertIn("Stdout message", result.stdout)
        self.assertIn("Stderr message", result.stdout)
        
        # Now run the actual pipeline test with our implementation
        # Create test script for the pipeline executor
        pipeline_test = f"""
import os
import sys
from src.parser import tokenize
from src.execution.pipeline import PipelineExecutor

# Create an output file path
output_file = "{os.path.join(self.temp_dir.name, "pipeline_output.txt")}"

# Create a script that writes to stdout and stderr
script_content = '''
import sys
print("Stdout message")
print("Stderr message", file=sys.stderr)
'''

script_path = "{os.path.join(self.temp_dir.name, "test_output.py")}"
with open(script_path, 'w') as f:
    f.write(script_content)

# Create a command with 2>&1 redirection
cmd = f"python3 {{script_path}} > {{output_file}} 2>&1"
print(f"Executing command: {{cmd}}")

# Execute the command through our pipeline executor
executor = PipelineExecutor(interactive=False)
executor.execute_pipeline(tokenize(cmd))

# Print the output file contents
print("\\nOutput file contents:")
with open(output_file, 'r') as f:
    print(f.read())
"""
        pipeline_path = os.path.join(self.temp_dir.name, "pipeline_test.py")
        with open(pipeline_path, 'w') as f:
            f.write(pipeline_test)
        
        # Run the pipeline test
        pipeline_result = subprocess.run([sys.executable, pipeline_path], capture_output=True, text=True)
        
        # Print the output for debugging
        print("Pipeline test stdout:", pipeline_result.stdout)
        print("Pipeline test stderr:", pipeline_result.stderr)
        
        # Check output file for both messages
        output_file = os.path.join(self.temp_dir.name, "pipeline_output.txt")
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn("Stdout message", content, "Stdout message not found in output file")
            self.assertIn("Stderr message", content, "Stderr message not found in output file")
            
if __name__ == '__main__':
    unittest.main()