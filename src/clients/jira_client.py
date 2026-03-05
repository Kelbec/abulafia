"""Jira API client for fetching issues and project data."""
from jira import JIRA
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..config import Config


class JiraClient:
    """Client for interacting with Jira API."""
    
    def __init__(self):
        """Initialize Jira client with configuration."""
        self.jira = JIRA(
            server=Config.JIRA_SERVER,
            basic_auth=(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN),
            options={'server': Config.JIRA_SERVER, 'rest_api_version': 3}
        )
        
        # Load projects from config.json if available, otherwise use legacy .env values
        Config.load_config_file()
        projects = Config.get_projects()
        
        if projects and len(projects) > 0:
            # Use first enabled project as default
            default_project = projects[0]
            self.project_key = default_project['key']
            self.board_id = default_project.get('board_id', '')
        else:
            # Fallback to legacy .env configuration
            self.project_key = Config.JIRA_PROJECT_KEY
            self.board_id = Config.JIRA_BOARD_ID
    
    def test_connection(self) -> bool:
        """Test if Jira connection is working."""
        try:
            self.jira.myself()
            return True
        except Exception as e:
            print(f"Jira connection failed: {e}")
            return False
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user information."""
        return self.jira.myself()
    
    def get_issues_by_jql(self, jql: str, max_results: int = 50) -> List[Any]:
        """
        Fetch issues using JQL query.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Jira issues
        """
        return self.jira.search_issues(jql, maxResults=max_results)
    
    def get_assigned_issues(self, assignee: Optional[str] = None, max_results: int = 50) -> List[Any]:
        """
        Get issues assigned to a specific user.
        
        Args:
            assignee: Username or email. If None, uses current user
            max_results: Maximum number of results
            
        Returns:
            List of assigned issues
        """
        if assignee is None:
            assignee = "currentUser()"
        else:
            assignee = f'"{assignee}"'
            
        jql = f"assignee = {assignee} AND resolution = Unresolved ORDER BY priority DESC, updated DESC"
        return self.get_issues_by_jql(jql, max_results)
    
    def get_sprint_issues(self, sprint_id: Optional[int] = None) -> List[Any]:
        """
        Get issues in a specific sprint or current sprint.
        
        Args:
            sprint_id: Sprint ID. If None, gets active sprint issues
            
        Returns:
            List of sprint issues
        """
        if sprint_id:
            jql = f"sprint = {sprint_id} ORDER BY rank"
        else:
            # Get active sprint issues
            if self.board_id:
                jql = f"sprint in openSprints() AND board = {self.board_id} ORDER BY rank"
            else:
                jql = "sprint in openSprints() ORDER BY rank"
        
        return self.get_issues_by_jql(jql, max_results=100)
    
    def get_issues_due_this_week(self) -> List[Any]:
        """Get issues due within the current week."""
        start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        start_str = start_of_week.strftime('%Y-%m-%d')
        end_str = end_of_week.strftime('%Y-%m-%d')
        
        jql = f"duedate >= '{start_str}' AND duedate <= '{end_str}' AND resolution = Unresolved ORDER BY duedate ASC"
        return self.get_issues_by_jql(jql, max_results=50)
    
    def get_recently_updated_issues(self, days: int = 7) -> List[Any]:
        """
        Get issues updated in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recently updated issues
        """
        jql = f"updated >= -{days}d ORDER BY updated DESC"
        return self.get_issues_by_jql(jql, max_results=50)
    
    def get_issues_by_status(self, status: str, max_results: int = 50) -> List[Any]:
        """
        Get issues by status.
        
        Args:
            status: Status name (e.g., "In Progress", "To Do")
            max_results: Maximum number of results
            
        Returns:
            List of issues with the specified status
        """
        jql = f'status = "{status}" AND assignee = currentUser() ORDER BY priority DESC'
        return self.get_issues_by_jql(jql, max_results)
    
    def get_project_info(self, project_key: Optional[str] = None) -> Any:
        """Get project information."""
        key = project_key or self.project_key
        if not key:
            raise ValueError("No project key provided")
        return self.jira.project(key)
    
    def format_issue(self, issue: Any) -> Dict[str, Any]:
        """
        Format Jira issue into a dictionary with relevant information.
        
        Args:
            issue: Jira issue object
            
        Returns:
            Formatted issue dictionary
        """
        return {
            'key': issue.key,
            'summary': issue.fields.summary,
            'status': issue.fields.status.name,
            'priority': issue.fields.priority.name if issue.fields.priority else 'None',
            'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
            'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
            'created': issue.fields.created,
            'updated': issue.fields.updated,
            'description': issue.fields.description if issue.fields.description else '',
            'issue_type': issue.fields.issuetype.name,
            'duedate': issue.fields.duedate if hasattr(issue.fields, 'duedate') else None,
            'labels': issue.fields.labels if issue.fields.labels else [],
            'url': f"{Config.JIRA_SERVER}/browse/{issue.key}"
        }
    
    def get_team_members(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all team members from a project.
        
        Args:
            project_key: Project key. If None, uses configured project
            
        Returns:
            List of user dictionaries
        """
        key = project_key or self.project_key
        if not key:
            # Get all users who have been assigned issues
            jql = "assignee is not EMPTY ORDER BY assignee"
            issues = self.get_issues_by_jql(jql, max_results=1000)
            
            # Extract unique assignees
            users = {}
            for issue in issues:
                if issue.fields.assignee:
                    user_key = issue.fields.assignee.accountId
                    if user_key not in users:
                        users[user_key] = {
                            'accountId': issue.fields.assignee.accountId,
                            'displayName': issue.fields.assignee.displayName,
                            'emailAddress': getattr(issue.fields.assignee, 'emailAddress', 'N/A')
                        }
            return list(users.values())
        else:
            # Get project-specific assignees
            jql = f'project = "{key}" AND assignee is not EMPTY ORDER BY assignee'
            issues = self.get_issues_by_jql(jql, max_results=1000)
            
            users = {}
            for issue in issues:
                if issue.fields.assignee:
                    user_key = issue.fields.assignee.accountId
                    if user_key not in users:
                        users[user_key] = {
                            'accountId': issue.fields.assignee.accountId,
                            'displayName': issue.fields.assignee.displayName,
                            'emailAddress': getattr(issue.fields.assignee, 'emailAddress', 'N/A')
                        }
            return list(users.values())
    
    def get_team_issues(self, project_key: Optional[str] = None, max_results: int = 100) -> List[Any]:
        """
        Get all issues for the team/project.
        
        Args:
            project_key: Project key. If None, uses configured project
            max_results: Maximum number of results
            
        Returns:
            List of all team issues
        """
        key = project_key or self.project_key
        if key:
            jql = f'project = "{key}" AND resolution = Unresolved ORDER BY priority DESC, updated DESC'
        else:
            jql = "resolution = Unresolved ORDER BY priority DESC, updated DESC"
        
        return self.get_issues_by_jql(jql, max_results)
    
    def get_issues_completed_in_period(self, start_date: datetime, end_date: datetime, 
                                       project_key: Optional[str] = None) -> List[Any]:
        """
        Get issues completed within a date range.
        
        Args:
            start_date: Start of period
            end_date: End of period
            project_key: Project key. If None, uses configured project or all projects
            
        Returns:
            List of completed issues
        """
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        key = project_key or self.project_key
        if key:
            jql = f'project = "{key}" AND resolved >= "{start_str}" AND resolved <= "{end_str}" ORDER BY resolved DESC'
        else:
            jql = f'resolved >= "{start_str}" AND resolved <= "{end_str}" ORDER BY resolved DESC'
        
        return self.get_issues_by_jql(jql, max_results=200)
    
    def get_issues_updated_in_period(self, start_date: datetime, end_date: datetime,
                                     project_key: Optional[str] = None) -> List[Any]:
        """
        Get issues updated within a date range.
        
        Args:
            start_date: Start of period
            end_date: End of period
            project_key: Project key. If None, uses configured project or all projects
            
        Returns:
            List of updated issues
        """
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        key = project_key or self.project_key
        if key:
            jql = f'project = "{key}" AND updated >= "{start_str}" AND updated <= "{end_str}" ORDER BY updated DESC'
        else:
            jql = f'updated >= "{start_str}" AND updated <= "{end_str}" ORDER BY updated DESC'
        
        return self.get_issues_by_jql(jql, max_results=200)
    
    def get_issues_created_in_period(self, start_date: datetime, end_date: datetime,
                                     project_key: Optional[str] = None) -> List[Any]:
        """
        Get issues created within a date range.
        
        Args:
            start_date: Start of period
            end_date: End of period
            project_key: Project key. If None, uses configured project or all projects
            
        Returns:
            List of created issues
        """
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        key = project_key or self.project_key
        if key:
            jql = f'project = "{key}" AND created >= "{start_str}" AND created <= "{end_str}" ORDER BY created DESC'
        else:
            jql = f'created >= "{start_str}" AND created <= "{end_str}" ORDER BY created DESC'
        
        return self.get_issues_by_jql(jql, max_results=200)
    
    def get_stale_issues(self, days: int = 7, project_key: Optional[str] = None) -> List[Any]:
        """
        Get issues that haven't been updated in X days.
        
        Args:
            days: Number of days threshold
            project_key: Project key. If None, uses configured project
            
        Returns:
            List of stale issues
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        key = project_key or self.project_key
        
        if key:
            jql = f'project = "{key}" AND resolution = Unresolved AND updated < "{cutoff_date}" ORDER BY updated ASC'
        else:
            jql = f'resolution = Unresolved AND updated < "{cutoff_date}" ORDER BY updated ASC'
        
        return self.get_issues_by_jql(jql, max_results=100)
    
    def get_aging_in_progress_issues(self, days: int = 14, project_key: Optional[str] = None) -> List[Any]:
        """
        Get issues that have been in progress for too long.
        
        Args:
            days: Number of days threshold
            project_key: Project key. If None, uses configured project
            
        Returns:
            List of aging in-progress issues
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        key = project_key or self.project_key
        
        if key:
            jql = f'project = "{key}" AND status = "In Progress" AND updated < "{cutoff_date}" ORDER BY updated ASC'
        else:
            jql = f'status = "In Progress" AND updated < "{cutoff_date}" ORDER BY updated ASC'
        
        return self.get_issues_by_jql(jql, max_results=100)
    
    def calculate_days_since_update(self, issue: Any) -> int:
        """
        Calculate days since issue was last updated.
        
        Args:
            issue: Jira issue object
            
        Returns:
            Number of days since last update
        """
        updated_str = issue.fields.updated
        # Parse Jira datetime format (e.g., "2024-03-01T10:30:00.000+0000")
        updated_date = datetime.strptime(updated_str[:19], '%Y-%m-%dT%H:%M:%S')
        days_diff = (datetime.now() - updated_date).days
        return days_diff
    
    def calculate_days_since_creation(self, issue: Any) -> int:
        """
        Calculate days since issue was created.
        
        Args:
            issue: Jira issue object
            
        Returns:
            Number of days since creation
        """
        created_str = issue.fields.created
        # Parse Jira datetime format
        created_date = datetime.strptime(created_str[:19], '%Y-%m-%dT%H:%M:%S')
        days_diff = (datetime.now() - created_date).days
        return days_diff
    
    def get_multi_project_issues(self, project_keys: List[str], max_results: int = 100) -> List[Any]:
        """
        Get issues across multiple projects.
        
        Args:
            project_keys: List of project keys
            max_results: Maximum number of results per project
            
        Returns:
            Combined list of issues from all projects
        """
        all_issues = []
        
        for key in project_keys:
            try:
                jql = f'project = "{key}" AND resolution = Unresolved ORDER BY priority DESC, updated DESC'
                issues = self.get_issues_by_jql(jql, max_results)
                all_issues.extend(issues)
            except Exception as e:
                print(f"Warning: Could not fetch issues from project {key}: {e}")
        
        return all_issues
    
    def get_multi_project_team_members(self, project_keys: List[str]) -> List[Dict[str, Any]]:
        """
        Get all unique team members across multiple projects.
        
        Args:
            project_keys: List of project keys
            
        Returns:
            List of unique user dictionaries
        """
        all_users = {}
        
        for key in project_keys:
            try:
                members = self.get_team_members(project_key=key)
                for member in members:
                    user_id = member['accountId']
                    if user_id not in all_users:
                        all_users[user_id] = member
            except Exception as e:
                print(f"Warning: Could not fetch team members from project {key}: {e}")
        
        return list(all_users.values())
    
    def get_multi_project_completed_in_period(self, project_keys: List[str], 
                                               start_date: datetime, end_date: datetime) -> List[Any]:
        """
        Get completed issues across multiple projects in a date range.
        
        Args:
            project_keys: List of project keys
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Combined list of completed issues
        """
        all_completed = []
        
        for key in project_keys:
            try:
                issues = self.get_issues_completed_in_period(start_date, end_date, project_key=key)
                all_completed.extend(issues)
            except Exception as e:
                print(f"Warning: Could not fetch completed issues from project {key}: {e}")
        
        return all_completed
    
    def get_multi_project_updated_in_period(self, project_keys: List[str],
                                             start_date: datetime, end_date: datetime) -> List[Any]:
        """
        Get updated issues across multiple projects in a date range.
        
        Args:
            project_keys: List of project keys
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Combined list of updated issues
        """
        all_updated = []
        
        for key in project_keys:
            try:
                issues = self.get_issues_updated_in_period(start_date, end_date, project_key=key)
                all_updated.extend(issues)
            except Exception as e:
                print(f"Warning: Could not fetch updated issues from project {key}: {e}")
        
        return all_updated
    
    def get_multi_project_created_in_period(self, project_keys: List[str],
                                             start_date: datetime, end_date: datetime) -> List[Any]:
        """
        Get created issues across multiple projects in a date range.
        
        Args:
            project_keys: List of project keys
            start_date: Start of period
            end_date: End of period
            
        Returns:
            Combined list of created issues
        """
        all_created = []
        
        for key in project_keys:
            try:
                issues = self.get_issues_created_in_period(start_date, end_date, project_key=key)
                all_created.extend(issues)
            except Exception as e:
                print(f"Warning: Could not fetch created issues from project {key}: {e}")
        
        return all_created
    
    def get_multi_project_stale_issues(self, project_keys: List[str], days: int = 7) -> List[Any]:
        """
        Get stale issues across multiple projects.
        
        Args:
            project_keys: List of project keys
            days: Number of days threshold
            
        Returns:
            Combined list of stale issues
        """
        all_stale = []
        
        for key in project_keys:
            try:
                issues = self.get_stale_issues(days=days, project_key=key)
                all_stale.extend(issues)
            except Exception as e:
                print(f"Warning: Could not fetch stale issues from project {key}: {e}")
        
        return all_stale
    
    def get_multi_project_aging_in_progress(self, project_keys: List[str], days: int = 14) -> List[Any]:
        """
        Get aging in-progress issues across multiple projects.
        
        Args:
            project_keys: List of project keys
            days: Number of days threshold
            
        Returns:
            Combined list of aging issues
        """
        all_aging = []
        
        for key in project_keys:
            try:
                issues = self.get_aging_in_progress_issues(days=days, project_key=key)
                all_aging.extend(issues)
            except Exception as e:
                print(f"Warning: Could not fetch aging issues from project {key}: {e}")
        
        return all_aging
