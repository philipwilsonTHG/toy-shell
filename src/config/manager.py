#!/usr/bin/env python3

import os
import sys
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages shell configuration"""
    
    DEFAULT_CONFIG = {
        'histsize': 10000,
        'histfile': '~/.psh_history',
        'debug': False,
        'prompt_template': '\\[blue]\\u@\\h\\[reset]:\\[cyan]\\w\\[reset] \\[green]\\g\\[reset]\\$ '
    }
    
    def __init__(self):
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from ~/.pshrc"""
        rcfile = os.path.expanduser("~/.pshrc")
        
        if os.path.exists(rcfile):
            try:
                with open(rcfile) as f:
                    self._parse_config_file(f)
            except Exception as e:
                print(f"Error loading config: {e}", file=sys.stderr)
        
        return self.config
    
    def _parse_config_file(self, file_obj):
        """Parse configuration file contents"""
        for line in file_obj:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Handle configuration directives
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Convert to appropriate type
                if value.lower() in ('true', 'yes', 'on'):
                    value = True
                elif value.lower() in ('false', 'no', 'off'):
                    value = False
                elif value.isdigit():
                    value = int(value)
                
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value"""
        self.config[key] = value
    
    def generate_prompt(self) -> str:
        """Generate the shell prompt based on configuration"""
        from ..utils.prompt import PromptFormatter
        
        template = self.config.get('prompt_template')
        formatter = PromptFormatter()
        
        # Handle old format templates for backwards compatibility
        if '{' in template and '}' in template:
            # Legacy format string style prompt
            home = os.path.expanduser("~")
            cwd = os.getcwd().replace(home, "~")
            
            return template.format(
                user=os.getlogin(),
                host=os.uname().nodename,
                cwd=cwd
            )
        
        # Use the new prompt formatter
        return formatter.format(template)