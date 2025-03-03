#!/usr/bin/env python3

import os
import sys
import signal
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum, auto


class JobStatus(Enum):
    RUNNING = auto()
    STOPPED = auto()
    DONE = auto()


@dataclass
class Job:
    id: int
    pgid: int
    command: str
    status: JobStatus
    processes: List[int]


class ShellContext:
    """Global shell context managing state and configuration"""
    
    def __init__(self):
        self.jobs: Dict[int, Job] = {}
        self.next_job_id: int = 1
        
        # Initialize current working directory tracking
        current_dir = os.getcwd()
        self.cwd_history: List[str] = [current_dir]
        
        # Initialize OLDPWD environment variable
        if "OLDPWD" not in os.environ:
            os.environ["OLDPWD"] = current_dir
        
        self.interactive: bool = sys.stdin.isatty()
        self.debug: bool = False
        self.logger = self.setup_logging()
        
        # History configuration
        self.histfile = os.path.expanduser("~/.psh_history")
        self.histsize = 10000
        
    def setup_logging(self) -> logging.Logger:
        """Set up logging configuration"""
        logger = logging.getLogger('psh')
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def update_job_status(self):
        """Update status of all jobs"""
        for job in self.jobs.values():
            if job.status == JobStatus.DONE:
                continue
            
            alive = False
            for pid in job.processes:
                try:
                    os.kill(pid, 0)
                    alive = True
                    break
                except ProcessLookupError:
                    continue
            
            if not alive:
                job.status = JobStatus.DONE
    
    def cleanup_jobs(self):
        """Remove completed jobs"""
        done_jobs = [jid for jid, job in self.jobs.items() 
                    if job.status == JobStatus.DONE]
        for jid in done_jobs:
            del self.jobs[jid]
    
    def add_job(self, command: str, pgid: int, processes: List[int], 
                background: bool = False) -> Job:
        """Add a new job to the job table"""
        job = Job(
            id=self.next_job_id,
            pgid=pgid,
            command=command,
            status=JobStatus.RUNNING,
            processes=processes
        )
        self.jobs[job.id] = job
        self.next_job_id += 1
        return job
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def format_job_status(self, job: Job) -> str:
        """Format job status for display"""
        status_str = {
            JobStatus.RUNNING: "Running",
            JobStatus.STOPPED: "Stopped",
            JobStatus.DONE: "Done"
        }[job.status]
        
        return f"[{job.id}] {status_str}\t{job.command}"
    
    def get_prompt(self) -> str:
        """Generate shell prompt based on configuration"""
        home = os.path.expanduser("~")
        cwd = os.getcwd().replace(home, "~")
        
        return f"{os.getlogin()}@{os.uname().nodename}:{cwd}$ "


# Global shell context instance
SHELL = ShellContext()