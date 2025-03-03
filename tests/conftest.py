#!/usr/bin/env python3

import os
import sys
import tempfile
import pytest
import readline
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import shell modules
from src.context import SHELL, Job, JobStatus
from src.utils.history import HistoryManager

# Mark as running in pytest
os.environ['PYTEST_RUNNING'] = '1'


@pytest.fixture(autouse=True)
def reset_job_status():
    """Reset job status before and after each test"""
    # Save original jobs
    original_jobs = SHELL.jobs.copy()
    SHELL.jobs.clear()
    
    yield
    
    # Restore original jobs
    SHELL.jobs.clear()
    SHELL.jobs.update(original_jobs)


@pytest.fixture
def setup_env():
    """Set up environment variables for testing"""
    old_env = os.environ.copy()
    os.environ.update({
        'TEST_VAR': 'test_value',
        'PATH': '/bin:/usr/bin',
        'HOME': '/home/test'
    })
    yield
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def setup_history():
    """Set up history for testing"""
    # Clear existing history
    readline.clear_history()
    
    # Add test entries
    test_commands = ["ls", "cd /tmp", "echo hello", "grep pattern file"]
    for cmd in test_commands:
        readline.add_history(cmd)
    
    yield
    
    # Clean up
    readline.clear_history()


@pytest.fixture
def temp_home(tmp_path):
    """Create a temporary home directory"""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    old_home = os.environ.get('HOME')
    os.environ['HOME'] = str(home_dir)
    yield str(home_dir)
    if old_home:
        os.environ['HOME'] = old_home
    else:
        del os.environ['HOME']


@pytest.fixture
def running_job():
    """Create a dummy running job"""
    job = Job(id=1, pgid=12345, command='sleep 100', status=JobStatus.RUNNING, processes=[12345])
    SHELL.jobs[job.id] = job
    yield job
    if job.id in SHELL.jobs:
        del SHELL.jobs[job.id]


@pytest.fixture
def stopped_job():
    """Create a dummy stopped job"""
    job = Job(id=4, pgid=25679, command='sleep 100', status=JobStatus.STOPPED, processes=[25679])
    SHELL.jobs[job.id] = job
    yield job
    if job.id in SHELL.jobs:
        del SHELL.jobs[job.id]