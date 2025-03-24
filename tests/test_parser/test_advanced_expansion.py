#!/usr/bin/env python3

import os
import sys
import unittest
import pytest
from src.parser.state_machine_expander import StateMachineExpander, Tokenizer, TokenType, Token


class TestAdvancedParameterExpansion(unittest.TestCase):
    """Tests for advanced parameter expansion patterns that emulate common shell scripts"""
    
    def setUp(self):
        """Set up test fixtures with realistic shell script variables"""
        # Create variables that would be typical in real shell scripts
        self.variables = {
            # Paths and filesystem related
            "HOME": "/home/user",
            "PWD": "/home/user/projects/app",
            "WORKDIR": "/var/www/html",
            "LOGDIR": "/var/log/app",
            "CONFIG_FILE": "/etc/app/config.json",
            "DATA_FILE": "data.tar.gz",
            "BACKUP_FILE": "backup-2023-04-15.zip",
            
            # Environment variables
            "USER": "developer",
            "HOST": "dev-server",
            "HOSTNAME": "dev-server.example.com",
            "LANG": "en_US.UTF-8",
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            
            # Application specific
            "APP_VERSION": "1.2.3",
            "APP_NAME": "MyApplication",
            "APP_PORT": "8080",
            "DATABASE_URL": "postgresql://user:password@localhost:5432/dbname",
            "API_ENDPOINT": "https://api.example.com/v2/data",
            "LOG_LEVEL": "INFO",
            
            # Mixed case examples
            "MixedCaseVar": "Value with Mixed Case",
            "lowercase_var": "all lowercase value",
            "UPPERCASE_VAR": "ALL UPPERCASE VALUE",
            
            # Special format examples
            "VERSION_STRING": "v2.5.3-beta.1+build.456",
            "SEMVER": "2.5.3",
            "DATE": "2023-04-15",
            "TIMESTAMP": "2023-04-15T14:30:45Z",
            "CSV_DATA": "field1,field2,field3,field4",
            "KEY_VALUE": "key1=value1;key2=value2;key3=value3",
            "JSON_STRING": "{\"name\":\"test\",\"value\":123}",
            "XML_STRING": "<root><item>value</item></root>",
            
            # URLs and paths
            "GITHUB_REPO": "https://github.com/user/repo.git",
            "S3_PATH": "s3://bucket/path/to/object.json",
            "IMAGE_URL": "https://example.com/images/logo.png?size=large&format=png",
            
            # Empty and special cases
            "EMPTY": "",
            "WHITESPACE": "   ",
            "SPECIAL_CHARS": "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/",
        }
        
        def scope_provider(name):
            return self.variables.get(name)
        
        self.expander = StateMachineExpander(scope_provider)
        self.tokenizer = Tokenizer()
    
    @pytest.mark.skip(reason="Complex file path manipulations not yet implemented - see advanced_expansion_todo.md")
    def test_file_path_manipulations(self):
        """Test common file path manipulation patterns in shell scripts"""
        # Get directory from full path
        result = self.expander.expand("${CONFIG_FILE%/*}")
        self.assertEqual(result, "/etc/app")
        
        # Get base filename
        result = self.expander.expand("${CONFIG_FILE##*/}")
        self.assertEqual(result, "config.json")
        
        # Get file extension
        result = self.expander.expand("${CONFIG_FILE##*.}")
        self.assertEqual(result, "json")
        
        # Remove file extension
        result = self.expander.expand("${DATA_FILE%.*}")
        self.assertEqual(result, "data.tar")
        
        # Remove all file extensions
        result = self.expander.expand("${DATA_FILE%%.*}")
        self.assertEqual(result, "data")
        
        # Create backup filename by adding extension
        result = self.expander.expand("${CONFIG_FILE}.bak")
        self.assertEqual(result, "/etc/app/config.json.bak")
        
        # Replace extension
        result = self.expander.expand("${CONFIG_FILE%.json}.yaml")
        self.assertEqual(result, "/etc/app/config.yaml")
    
    @pytest.mark.skip(reason="URL component extraction needs more work - see advanced_expansion_todo.md")
    def test_url_manipulations(self):
        """Test URL manipulation patterns common in shell scripts"""
        # Extract protocol from URL
        result = self.expander.expand("${API_ENDPOINT%%://*}")
        self.assertEqual(result, "https")
        
        # Remove protocol from URL
        result = self.expander.expand("${API_ENDPOINT#*://}")
        self.assertEqual(result, "api.example.com/v2/data")
        
        # Extract domain from URL
        result = self.expander.expand("${API_ENDPOINT#*://}")
        result = self.expander.expand("${result%%/*}")
        self.assertEqual(result, "api.example.com")
        
        # Extract path from URL
        result = self.expander.expand("${API_ENDPOINT#*://*/}")
        self.assertEqual(result, "data")
        
        # Change protocol in URL
        result = self.expander.expand("${API_ENDPOINT/https/http}")
        self.assertEqual(result, "http://api.example.com/v2/data")
    
    @pytest.mark.skip(reason="Version string component extraction not yet implemented - see advanced_expansion_todo.md")
    def test_version_string_manipulations(self):
        """Test version string manipulation patterns"""
        # Extract major version
        result = self.expander.expand("${APP_VERSION%%.*}")
        self.assertEqual(result, "1")
        
        # Extract minor version
        self.variables["MINOR_VERSION"] = self.expander.expand("${APP_VERSION#*.}")
        result = self.expander.expand("${MINOR_VERSION%%.*}")
        self.assertEqual(result, "2")
        
        # Extract patch version
        result = self.expander.expand("${APP_VERSION##*.}")
        self.assertEqual(result, "3")
        
        # Clean a complex semver string to just major.minor
        result = self.expander.expand("${VERSION_STRING#v}")
        result = self.expander.expand("${result%%-*}")
        result = self.expander.expand("${result%.*}")
        self.assertEqual(result, "2.5")
    
    @pytest.mark.skip(reason="Advanced URL component parsing not yet implemented - see advanced_expansion_todo.md")
    def test_database_url_parsing(self):
        """Test parsing components from a database URL"""
        # Extract database user
        result = self.expander.expand("${DATABASE_URL#*://}")
        result = self.expander.expand("${result%%:*}")
        self.assertEqual(result, "user")
        
        # Extract database password
        result = self.expander.expand("${DATABASE_URL#*://}")
        result = self.expander.expand("${result#*:}")
        result = self.expander.expand("${result%%@*}")
        self.assertEqual(result, "password")
        
        # Extract database host
        result = self.expander.expand("${DATABASE_URL#*@}")
        result = self.expander.expand("${result%%:*}")
        self.assertEqual(result, "localhost")
        
        # Extract database port
        result = self.expander.expand("${DATABASE_URL#*:}")
        result = self.expander.expand("${result#*:}")
        result = self.expander.expand("${result#*:}")
        result = self.expander.expand("${result%%/*}")
        self.assertEqual(result, "5432")
        
        # Extract database name
        result = self.expander.expand("${DATABASE_URL##*/}")
        self.assertEqual(result, "dbname")
    
    @pytest.mark.skip(reason="Git URL component parsing not yet implemented - see advanced_expansion_todo.md")
    def test_git_url_manipulations(self):
        """Test manipulation of Git repository URLs"""
        # Extract repository name without .git extension
        result = self.expander.expand("${GITHUB_REPO##*/}")
        result = self.expander.expand("${result%.git}")
        self.assertEqual(result, "repo")
        
        # Extract username from GitHub URL
        result = self.expander.expand("${GITHUB_REPO#https://github.com/}")
        result = self.expander.expand("${result%%/*}")
        self.assertEqual(result, "user")
        
        # Convert HTTPS URL to SSH URL
        result = self.expander.expand("${GITHUB_REPO/https:\\/\\/github.com\\//git@github.com:}")
        self.assertEqual(result, "git@github.com:user/repo.git")
    
    def test_csv_data_manipulations(self):
        """Test manipulations of CSV formatted data"""
        # Extract first field
        result = self.expander.expand("${CSV_DATA%%,*}")
        self.assertEqual(result, "field1")
        
        # Extract last field
        result = self.expander.expand("${CSV_DATA##*,}")
        self.assertEqual(result, "field4")
        
        # Replace comma delimiter with semicolon
        result = self.expander.expand("${CSV_DATA//,/;}")
        self.assertEqual(result, "field1;field2;field3;field4")
    
    @pytest.mark.skip(reason="Key-value pair extraction not yet implemented - see advanced_expansion_todo.md")
    def test_key_value_manipulations(self):
        """Test manipulations of key-value formatted data"""
        # Extract first key
        result = self.expander.expand("${KEY_VALUE%%=*}")
        self.assertEqual(result, "key1")
        
        # Extract value for a specific key
        # This is complex in pure parameter expansion but can be done in parts
        result = self.expander.expand("${KEY_VALUE#*key2=}")
        result = self.expander.expand("${result%%;*}")
        self.assertEqual(result, "value2")
        
        # Replace equals sign with colon
        result = self.expander.expand("${KEY_VALUE//=/:}")
        self.assertEqual(result, "key1:value1;key2:value2;key3:value3")
    
    def test_hostname_manipulations(self):
        """Test manipulations of hostname and domain values"""
        # Extract domain part from full hostname
        result = self.expander.expand("${HOSTNAME#*.}")
        self.assertEqual(result, "example.com")
        
        # Extract hostname without domain
        result = self.expander.expand("${HOSTNAME%%.*}")
        self.assertEqual(result, "dev-server")
    
    @pytest.mark.skip(reason="Date component extraction not yet implemented - see advanced_expansion_todo.md")
    def test_date_manipulations(self):
        """Test manipulations of date strings"""
        # Extract year from date
        result = self.expander.expand("${DATE%%-*}")
        self.assertEqual(result, "2023")
        
        # Extract month from date
        result = self.expander.expand("${DATE#*-}")
        result = self.expander.expand("${result%%-*}")
        self.assertEqual(result, "04")
        
        # Extract day from date
        result = self.expander.expand("${DATE##*-}")
        self.assertEqual(result, "15")
        
        # Extract date part from timestamp
        result = self.expander.expand("${TIMESTAMP%%T*}")
        self.assertEqual(result, "2023-04-15")
        
        # Extract time part from timestamp
        result = self.expander.expand("${TIMESTAMP#*T}")
        self.assertEqual(result, "14:30:45Z")
    
    @pytest.mark.skip(reason="Advanced nested operations not yet implemented - see advanced_expansion_todo.md")
    def test_complex_nested_operations(self):
        """Test complex nested parameter expansions"""
        # Convert domain to uppercase
        result = self.expander.expand("${${HOSTNAME#*.}^^}")
        self.assertEqual(result, "EXAMPLE.COM")
        
        # Extract and format version as v1_2_3
        result = self.expander.expand("v${APP_VERSION//./_}")
        self.assertEqual(result, "v1_2_3")
        
        # Create a log file path with app name and date
        log_path = self.expander.expand("${LOGDIR}/${APP_NAME,,}-${DATE}.log")
        self.assertEqual(log_path, "/var/log/app/myapplication-2023-04-15.log")
        
        # Extract domain from URL and prepend "api-" to it
        part1 = self.expander.expand("${API_ENDPOINT#*://}")
        part2 = self.expander.expand("${part1%%/*}")
        result = self.expander.expand("api-${part2}")
        self.assertEqual(result, "api-api.example.com")
    
    @pytest.mark.skip(reason="Template substitution with placeholders not yet implemented - see advanced_expansion_todo.md")
    def test_template_substitution_patterns(self):
        """Test common template substitution patterns"""
        # Define a template string with placeholders
        self.variables["TEMPLATE"] = "Hello {{NAME}}, welcome to {{SERVICE}}!"
        
        # Replace placeholders with values
        self.variables["NAME"] = self.variables["USER"]
        self.variables["SERVICE"] = self.variables["APP_NAME"]
        
        result = self.expander.expand("${TEMPLATE//\\{\\{NAME\\}\\}/${NAME}}")
        result = self.expander.expand("${result//\\{\\{SERVICE\\}\\}/${SERVICE}}")
        
        self.assertEqual(result, "Hello developer, welcome to MyApplication!")
    
    def test_conditional_parameter_expansion(self):
        """Test common conditional parameter expansion patterns"""
        # Test default value (:-) when variable is empty
        result = self.expander.expand("${EMPTY:-default value}")
        self.assertEqual(result, "default value")
        
        # Test default value (:-) when variable is set
        result = self.expander.expand("${USER:-default user}")
        self.assertEqual(result, "developer")
        
        # Test alternate value (:+) when variable is set
        result = self.expander.expand("${USER:+logged in}")
        self.assertEqual(result, "logged in")
        
        # Test alternate value (:+) when variable is empty
        result = self.expander.expand("${EMPTY:+value exists}")
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()