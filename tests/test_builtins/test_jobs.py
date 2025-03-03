#!/usr/bin/env python3

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.context import SHELL, JobStatus, Job
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


def test_jobs_list(capsys):
    """Test jobs command with one job"""
    # Patch update_job_status to prevent auto-marking as DONE
    with patch('src.context.ShellContext.update_job_status'):
        # Create a job directly in the test
        SHELL.jobs.clear()
        job = Job(id=1, pgid=12345, command='sleep 100', status=JobStatus.RUNNING, processes=[12345])
        SHELL.jobs[job.id] = job
        
        try:
            jobs()
            captured = capsys.readouterr()
            
            assert f"[{job.id}]" in captured.out
            assert "Running" in captured.out
            assert job.command in captured.out
        finally:
            # Clean up
            SHELL.jobs.clear()


def test_jobs_multiple(capsys):
    """Test jobs command with multiple jobs"""
    # Patch update_job_status to prevent auto-marking as DONE
    with patch('src.context.ShellContext.update_job_status'):
        # Create jobs directly in the test
        SHELL.jobs.clear()
        running_job = Job(id=1, pgid=12345, command='sleep 100', status=JobStatus.RUNNING, processes=[12345])
        stopped_job = Job(id=2, pgid=25679, command='sleep 200', status=JobStatus.STOPPED, processes=[25679])
        SHELL.jobs[running_job.id] = running_job
        SHELL.jobs[stopped_job.id] = stopped_job
        
        try:
            jobs()
            captured = capsys.readouterr()
            
            assert f"[{running_job.id}]" in captured.out
            assert f"[{stopped_job.id}]" in captured.out
            assert "Running" in captured.out
            assert "Stopped" in captured.out
        finally:
            # Clean up
            SHELL.jobs.clear()
    

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


def test_bg_resume_job(capsys):
    """Test resuming a stopped job"""
    # Patch update_job_status to prevent auto-marking as DONE
    with patch('src.context.ShellContext.update_job_status'):
        # Create a stopped job directly in the test
        SHELL.jobs.clear()
        job = Job(id=4, pgid=25679, command='sleep 100', status=JobStatus.STOPPED, processes=[25679])
        SHELL.jobs[job.id] = job
        
        try:
            bg(str(job.id))
            captured = capsys.readouterr()
            
            # In test mode, we don't actually change the job status
            # Just check that the output shows the job would be continued
            assert f"[{job.id}]" in captured.out
            assert f"{job.command}" in captured.out
            assert "&" in captured.out
        finally:
            # Clean up
            SHELL.jobs.clear()


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


def test_fg_bring_to_foreground(capsys):
    """Test foreground command"""
    # Patch update_job_status to prevent auto-marking as DONE
    with patch('src.context.ShellContext.update_job_status'):
        # Create a running job directly in the test
        SHELL.jobs.clear()
        job = Job(id=1, pgid=12345, command='sleep 100', status=JobStatus.RUNNING, processes=[12345])
        SHELL.jobs[job.id] = job
        
        try:
            result = fg(str(job.id))
            captured = capsys.readouterr()
            
            assert job.command in captured.out
            assert result == 0
        finally:
            # Clean up
            SHELL.jobs.clear()


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