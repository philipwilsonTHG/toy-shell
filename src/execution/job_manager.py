#!/usr/bin/env python3

import os
import signal
from typing import List, Dict, Optional, Tuple

from ..context import SHELL, Job, JobStatus


class JobManager:
    """Manages shell job control"""
    
    def __init__(self):
        self.shell_pgid = os.getpgid(0)
    
    def update_job_statuses(self):
        """Update status of all jobs"""
        SHELL.update_job_status()
        SHELL.cleanup_jobs()
    
    def create_job(self, command: str, pgid: int, processes: List[int], 
                   background: bool = False) -> Job:
        """Create a new job"""
        return SHELL.add_job(command, pgid, processes, background)
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Get a job by ID"""
        return SHELL.get_job(job_id)
    
    def list_jobs(self) -> List[Job]:
        """Get a list of all jobs"""
        return list(SHELL.jobs.values())
    
    def format_job_info(self, job: Job) -> str:
        """Format job information for display"""
        return SHELL.format_job_status(job)
    
    def bring_to_foreground(self, job: Job) -> int:
        """Bring a job to the foreground"""
        from ..utils.terminal import TerminalController
        
        # Set job as foreground process group
        TerminalController.set_foreground_pgrp(job.pgid)
        
        # Continue the process if it was stopped
        if job.status == JobStatus.STOPPED:
            os.killpg(job.pgid, signal.SIGCONT)
            job.status = JobStatus.RUNNING
        
        # Wait for it to complete or stop
        status = self.wait_for_job(job)
        
        # Return terminal control to shell
        TerminalController.set_foreground_pgrp(self.shell_pgid)
        
        return status
    
    def continue_in_background(self, job: Job):
        """Continue a stopped job in the background"""
        if job.status == JobStatus.STOPPED:
            os.killpg(job.pgid, signal.SIGCONT)
            job.status = JobStatus.RUNNING
            print(f"[{job.id}] {job.command} &")
    
    def wait_for_job(self, job: Job) -> int:
        """Wait for all processes in a job to complete or stop"""
        remaining_processes = job.processes.copy()
        
        while remaining_processes:
            try:
                pid, status = os.waitpid(-1, os.WUNTRACED)
                
                if pid in remaining_processes:
                    remaining_processes.remove(pid)
                
                if os.WIFSTOPPED(status):
                    # Job was stopped
                    job.status = JobStatus.STOPPED
                    print(f"\nJob {job.id} stopped")
                    break
                    
                if os.WIFEXITED(status) and not remaining_processes:
                    # Last process exited
                    exit_status = os.WEXITSTATUS(status)
                    job.status = JobStatus.DONE
                    return exit_status
                    
            except ChildProcessError:
                break
            except KeyboardInterrupt:
                # Forward interrupt to job
                os.killpg(job.pgid, signal.SIGINT)
        
        return 0