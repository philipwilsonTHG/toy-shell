#!/usr/bin/env python3

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.context import SHELL, JobStatus
from src.builtins.jobs import jobs, fg, bg


def setup_function(function):
    """Set up function for each test"""
    # Ensure jobs have proper status for tests
    for job in SHELL.jobs.values():
        # Set running and stopped jobs to the correct status
        # Jobs are marked as done by default in the testing framework
        if 'running_job' in function.__name__:
            job.status = JobStatus.RUNNING
        elif 'stopped_job' in function.__name__ or 'bg_resume' in function.__name__:
            job.status = JobStatus.STOPPED


def test_jobs_empty(capsys):
    """Test jobs command with no jobs"""
    # Clear jobs
    SHELL.jobs.clear()
    
    jobs()
    captured = capsys.readouterr()
    
    # Should produce no output with empty jobs list
    assert captured.out == ""
    assert captured.err == ""


def test_jobs_list(running_job, capsys):
    """Test jobs command with one job"""
    # Set job to running for the test
    running_job.status = JobStatus.RUNNING
    
    jobs()
    captured = capsys.readouterr()
    
    assert f"[{running_job.id}]" in captured.out
    assert "Running" in captured.out
    assert running_job.command in captured.out


def test_jobs_multiple(running_job, stopped_job, capsys):
    """Test jobs command with multiple jobs"""
    # Set job statuses for test
    running_job.status = JobStatus.RUNNING
    stopped_job.status = JobStatus.STOPPED
    
    jobs()
    captured = capsys.readouterr()
    
    assert f"[{running_job.id}]" in captured.out
    assert f"[{stopped_job.id}]" in captured.out
    assert "Running" in captured.out
    assert "Stopped" in captured.out
    

def test_bg_no_args(capsys):
    """Test bg command with no arguments"""
    bg()
    captured = capsys.readouterr()
    assert "no current job" in captured.err.lower()


def test_bg_invalid_job(capsys):
    """Test bg command with invalid job ID"""
    bg("999")
    captured = capsys.readouterr()
    assert "not found" in captured.err.lower()


def test_bg_resume_job(stopped_job, capsys):
    """Test resuming a stopped job"""
    # Ensure job is stopped
    stopped_job.status = JobStatus.STOPPED
    
    bg(str(stopped_job.id))
    captured = capsys.readouterr()
    
    # In test mode, we don't actually change the job status
    # Just check that the output shows the job would be continued
    assert f"[{stopped_job.id}]" in captured.out
    assert f"{stopped_job.command}" in captured.out
    assert "&" in captured.out


def test_fg_no_args(capsys):
    """Test fg command with no arguments"""
    fg()
    captured = capsys.readouterr()
    assert "no current job" in captured.err.lower()


def test_fg_invalid_job(capsys):
    """Test fg command with invalid job ID"""
    fg("999")
    captured = capsys.readouterr()
    assert "not found" in captured.err.lower()


def test_fg_bring_to_foreground(running_job, capsys):
    """Test foreground command"""
    # Ensure job is running
    running_job.status = JobStatus.RUNNING
    
    with patch('src.execution.job_manager.JobManager.bring_to_foreground', return_value=0):
        result = fg(str(running_job.id))
        captured = capsys.readouterr()
        
        assert running_job.command in captured.out
        assert result == 0


def test_cleanup_done_jobs():
    """Test job cleanup"""
    # Create a job marked as done
    done_job = MagicMock()
    done_job.id = 99
    done_job.status = JobStatus.DONE
    SHELL.jobs[done_job.id] = done_job
    
    # Call cleanup
    SHELL.cleanup_jobs()
    
    # Job should be removed
    assert done_job.id not in SHELL.jobs


def test_job_status_update():
    """Test job status update"""
    # Create a mock job
    mock_job = MagicMock()
    mock_job.status = JobStatus.RUNNING
    mock_job.processes = [12345]
    SHELL.jobs[999] = mock_job
    
    # Mock os.kill to simulate the process is gone
    with patch('os.kill', side_effect=ProcessLookupError):
        SHELL.update_job_status()
        
        # Job should be marked as done
        assert mock_job.status == JobStatus.DONE
        
    # Clean up
    if 999 in SHELL.jobs:
        del SHELL.jobs[999]