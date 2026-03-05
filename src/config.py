"""Configuration management for Abulafia Chatbot."""
import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for Jira and AI settings."""
    
    # Jira Configuration (credentials from .env)
    JIRA_SERVER = os.getenv('JIRA_SERVER')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
    
    # Legacy single project support (fallback)
    JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', '')
    JIRA_BOARD_ID = os.getenv('JIRA_BOARD_ID', '')
    
    # Multi-project configuration from config.json
    _config_data = None
    _projects = []
    _settings = {}
    
    @classmethod
    def load_config_file(cls) -> bool:
        """
        Load configuration from config.json file.
        
        Returns:
            True if config loaded successfully, False otherwise
        """
        # Config.json is in the parent directory (project root)
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    cls._config_data = json.load(f)
                    cls._projects = cls._config_data.get('projects', [])
                    cls._settings = cls._config_data.get('settings', {})
                    return True
            else:
                # If no config.json, create one with legacy project if available
                if cls.JIRA_PROJECT_KEY:
                    cls._projects = [{
                        'name': cls.JIRA_PROJECT_KEY,
                        'key': cls.JIRA_PROJECT_KEY,
                        'board_id': cls.JIRA_BOARD_ID,
                        'enabled': True,
                        'description': 'Default project from .env'
                    }]
                    cls._settings = {
                        'aggregate_reports': False,
                        'default_max_results': 200,
                        'stale_threshold_days': 7,
                        'aging_threshold_days': 14
                    }
                return False
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")
            # Fallback to legacy single project
            if cls.JIRA_PROJECT_KEY:
                cls._projects = [{
                    'name': cls.JIRA_PROJECT_KEY,
                    'key': cls.JIRA_PROJECT_KEY,
                    'board_id': cls.JIRA_BOARD_ID,
                    'enabled': True,
                    'description': 'Default project from .env'
                }]
            return False
    
    @classmethod
    def get_projects(cls) -> List[Dict[str, Any]]:
        """
        Get list of configured Jira projects.
        
        Returns:
            List of project dictionaries
        """
        if not cls._projects:
            cls.load_config_file()
        return [p for p in cls._projects if p.get('enabled', True)]
    
    @classmethod
    def get_all_projects(cls) -> List[Dict[str, Any]]:
        """
        Get all configured projects (including disabled ones).
        
        Returns:
            List of all project dictionaries
        """
        if not cls._projects:
            cls.load_config_file()
        return cls._projects
    
    @classmethod
    def get_project_by_key(cls, key: str) -> Dict[str, Any]:
        """
        Get project configuration by project key.
        
        Args:
            key: Project key (e.g., "MAR")
            
        Returns:
            Project dictionary or None if not found
        """
        projects = cls.get_all_projects()
        for project in projects:
            if project.get('key') == key:
                return project
        return None
    
    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
        """
        Get application settings.
        
        Returns:
            Settings dictionary
        """
        if not cls._settings:
            cls.load_config_file()
        return cls._settings
    
    @classmethod
    def is_aggregate_mode(cls) -> bool:
        """
        Check if aggregate reporting is enabled.
        
        Returns:
            True if aggregate mode is enabled
        """
        settings = cls.get_settings()
        return settings.get('aggregate_reports', False)
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        errors = []
        
        if not cls.JIRA_SERVER:
            errors.append("JIRA_SERVER is required")
        if not cls.JIRA_EMAIL:
            errors.append("JIRA_EMAIL is required")
        if not cls.JIRA_API_TOKEN:
            errors.append("JIRA_API_TOKEN is required")
            
        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"- {e}" for e in errors))
        
        return True
