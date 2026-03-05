"""Team and historical report generator for Jira data."""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from ..clients.jira_client import JiraClient


class ReportGenerator:
    """Generate team reports and historical activity reports."""
    
    def __init__(self, jira_client: JiraClient):
        """
        Initialize report generator.
        
        Args:
            jira_client: Instance of JiraClient
        """
        self.jira = jira_client
    
    def get_date_range(self, period: str = 'last_week') -> tuple:
        """
        Get start and end dates for a period.
        
        Args:
            period: 'last_week', 'last_month', 'current_week', 'current_month'
            
        Returns:
            Tuple of (start_date, end_date)
        """
        today = datetime.now()
        
        if period == 'last_week':
            # Previous Monday to Sunday
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            return last_monday, last_sunday
        
        elif period == 'last_month':
            # First day to last day of previous month
            first_of_this_month = today.replace(day=1)
            last_day_of_last_month = first_of_this_month - timedelta(days=1)
            first_of_last_month = last_day_of_last_month.replace(day=1)
            return first_of_last_month, last_day_of_last_month
        
        elif period == 'current_week':
            # This Monday to Sunday
            days_since_monday = today.weekday()
            this_monday = today - timedelta(days=days_since_monday)
            this_sunday = this_monday + timedelta(days=6)
            return this_monday, this_sunday
        
        elif period == 'current_month':
            # First day to last day of current month
            first_of_month = today.replace(day=1)
            # Get last day of current month
            if today.month == 12:
                last_of_month = today.replace(day=31)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
                last_of_month = next_month - timedelta(days=1)
            return first_of_month, last_of_month
        
        else:
            raise ValueError(f"Unknown period: {period}")
    
    def generate_team_report(self, project_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive team report showing all members' tasks.
        
        Args:
            project_keys: Optional list of project keys. If None, checks config for aggregate mode.
            
        Returns:
            Dictionary containing team report data with bottleneck detection
        """
        from ..config import Config
        
        # If no project_keys specified, check if we should use aggregate mode
        if project_keys is None:
            Config.load_config_file()
            projects = Config.get_projects()
            
            # If aggregate mode is enabled and multiple projects exist, use all
            if Config.is_aggregate_mode() and len(projects) > 1:
                project_keys = [p['key'] for p in projects]
            elif len(projects) == 1:
                # Single project from config
                project_keys = [projects[0]['key']]
            # else: project_keys stays None, will use JiraClient's default project_key
        
        # Multi-project or single-project mode
        if project_keys and len(project_keys) > 1:
            return self._generate_multi_project_team_report(project_keys)
        
        # Single project mode (original behavior)
        # Get team members
        team_members = self.jira.get_team_members()
        
        # Get all team issues
        team_issues = self.jira.get_team_issues(max_results=200)
        
        # Get bottleneck detection data
        stale_issues = self.jira.get_stale_issues(days=7)
        aging_in_progress = self.jira.get_aging_in_progress_issues(days=14)
        
        # Organize issues by assignee
        issues_by_assignee = defaultdict(list)
        issues_by_status = defaultdict(list)
        issues_by_priority = defaultdict(list)
        
        for issue in team_issues:
            issue_data = self.jira.format_issue(issue)
            issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
            issue_data['days_since_creation'] = self.jira.calculate_days_since_creation(issue)
            
            assignee = issue_data['assignee']
            status = issue_data['status']
            priority = issue_data['priority']
            
            issues_by_assignee[assignee].append(issue_data)
            issues_by_status[status].append(issue_data)
            issues_by_priority[priority].append(issue_data)
        
        # Calculate statistics per team member
        team_stats = {}
        for member in team_members:
            name = member['displayName']
            member_issues = issues_by_assignee.get(name, [])
            
            team_stats[name] = {
                'total_issues': len(member_issues),
                'by_status': defaultdict(int),
                'by_priority': defaultdict(int),
                'issues': member_issues
            }
            
            for issue in member_issues:
                team_stats[name]['by_status'][issue['status']] += 1
                team_stats[name]['by_priority'][issue['priority']] += 1
        
        # Bottleneck Detection Metrics
        bottlenecks = {
            'stale_issues': [],
            'aging_in_progress': [],
            'high_priority_at_risk': [],
            'workload_imbalance': [],
            'blocked_status': []
        }
        
        # Process stale issues
        for issue in stale_issues:
            issue_data = self.jira.format_issue(issue)
            issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
            bottlenecks['stale_issues'].append(issue_data)
        
        # Process aging in-progress issues
        for issue in aging_in_progress:
            issue_data = self.jira.format_issue(issue)
            issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
            issue_data['days_since_creation'] = self.jira.calculate_days_since_creation(issue)
            bottlenecks['aging_in_progress'].append(issue_data)
        
        # Identify high priority items at risk (high/highest priority, open > 14 days)
        high_priorities = issues_by_priority.get('Highest', []) + issues_by_priority.get('High', [])
        for issue in high_priorities:
            if issue['days_since_creation'] > 14 and 'Done' not in issue['status'] and 'Closed' not in issue['status']:
                bottlenecks['high_priority_at_risk'].append(issue)
        
        # Detect workload imbalance (members with significantly more issues than average)
        if team_members:
            avg_workload = len(team_issues) / len(team_members)
            threshold = avg_workload * 1.5  # 50% more than average
            
            for name, stats in team_stats.items():
                if stats['total_issues'] > threshold:
                    bottlenecks['workload_imbalance'].append({
                        'assignee': name,
                        'total_issues': stats['total_issues'],
                        'average': avg_workload,
                        'overload_percentage': ((stats['total_issues'] - avg_workload) / avg_workload * 100)
                    })
        
        # Identify blocked issues
        for issue in team_issues:
            if 'block' in issue.fields.status.name.lower():
                issue_data = self.jira.format_issue(issue)
                issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
                bottlenecks['blocked_status'].append(issue_data)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'team_members': team_members,
            'team_stats': team_stats,
            'issues_by_status': dict(issues_by_status),
            'total_team_issues': len(team_issues),
            'bottlenecks': bottlenecks,
            'summary': {
                'total_members': len(team_members),
                'total_issues': len(team_issues),
                'status_breakdown': {status: len(issues) for status, issues in issues_by_status.items()},
                'avg_workload': len(team_issues) / len(team_members) if team_members else 0,
                'total_stale': len(bottlenecks['stale_issues']),
                'total_aging': len(bottlenecks['aging_in_progress']),
                'total_at_risk': len(bottlenecks['high_priority_at_risk']),
                'total_overloaded': len(bottlenecks['workload_imbalance'])
            }
        }
    
    def _generate_multi_project_team_report(self, project_keys: List[str]) -> Dict[str, Any]:
        """
        Generate an aggregate team report across multiple projects.
        
        Args:
            project_keys: List of project keys to aggregate
            
        Returns:
            Dictionary containing aggregated team report data
        """
        from ..config import Config
        
        # Get team members across all projects
        team_members = self.jira.get_multi_project_team_members(project_keys)
        
        # Get all team issues from multiple projects
        team_issues = self.jira.get_multi_project_issues(project_keys, max_results=200)
        
        # Get bottleneck detection data from all projects
        settings = Config.get_settings()
        stale_threshold = settings.get('stale_threshold_days', 7)
        aging_threshold = settings.get('aging_threshold_days', 14)
        
        stale_issues = self.jira.get_multi_project_stale_issues(project_keys, days=stale_threshold)
        aging_in_progress = self.jira.get_multi_project_aging_in_progress(project_keys, days=aging_threshold)
        
        # Organize issues by assignee, status, priority, and project
        issues_by_assignee = defaultdict(list)
        issues_by_status = defaultdict(list)
        issues_by_priority = defaultdict(list)
        issues_by_project = defaultdict(list)
        
        for issue in team_issues:
            issue_data = self.jira.format_issue(issue)
            issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
            issue_data['days_since_creation'] = self.jira.calculate_days_since_creation(issue)
            
            # Extract project key from issue key (e.g., "MAR-123" -> "MAR")
            project_key = issue_data['key'].split('-')[0]
            issue_data['project_key'] = project_key
            
            assignee = issue_data['assignee']
            status = issue_data['status']
            priority = issue_data['priority']
            
            issues_by_assignee[assignee].append(issue_data)
            issues_by_status[status].append(issue_data)
            issues_by_priority[priority].append(issue_data)
            issues_by_project[project_key].append(issue_data)
        
        # Calculate statistics per team member
        team_stats = {}
        for member in team_members:
            name = member['displayName']
            member_issues = issues_by_assignee.get(name, [])
            
            team_stats[name] = {
                'total_issues': len(member_issues),
                'by_status': defaultdict(int),
                'by_priority': defaultdict(int),
                'by_project': defaultdict(int),
                'issues': member_issues
            }
            
            for issue in member_issues:
                team_stats[name]['by_status'][issue['status']] += 1
                team_stats[name]['by_priority'][issue['priority']] += 1
                team_stats[name]['by_project'][issue.get('project_key', 'Unknown')] += 1
        
        # Bottleneck Detection Metrics
        bottlenecks = {
            'stale_issues': [],
            'aging_in_progress': [],
            'high_priority_at_risk': [],
            'workload_imbalance': [],
            'blocked_status': []
        }
        
        # Process stale issues
        for issue in stale_issues:
            issue_data = self.jira.format_issue(issue)
            issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
            issue_data['project_key'] = issue_data['key'].split('-')[0]
            bottlenecks['stale_issues'].append(issue_data)
        
        # Process aging in-progress issues
        for issue in aging_in_progress:
            issue_data = self.jira.format_issue(issue)
            issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
            issue_data['days_since_creation'] = self.jira.calculate_days_since_creation(issue)
            issue_data['project_key'] = issue_data['key'].split('-')[0]
            bottlenecks['aging_in_progress'].append(issue_data)
        
        # Identify high priority items at risk
        high_priorities = issues_by_priority.get('Highest', []) + issues_by_priority.get('High', [])
        for issue in high_priorities:
            if issue['days_since_creation'] > 14 and 'Done' not in issue['status'] and 'Closed' not in issue['status']:
                bottlenecks['high_priority_at_risk'].append(issue)
        
        # Detect workload imbalance
        if team_members:
            avg_workload = len(team_issues) / len(team_members)
            threshold = avg_workload * 1.5
            
            for name, stats in team_stats.items():
                if stats['total_issues'] > threshold:
                    bottlenecks['workload_imbalance'].append({
                        'assignee': name,
                        'total_issues': stats['total_issues'],
                        'average': avg_workload,
                        'overload_percentage': ((stats['total_issues'] - avg_workload) / avg_workload * 100)
                    })
        
        # Identify blocked issues
        for issue in team_issues:
            if 'block' in issue.fields.status.name.lower():
                issue_data = self.jira.format_issue(issue)
                issue_data['days_since_update'] = self.jira.calculate_days_since_update(issue)
                issue_data['project_key'] = issue_data['key'].split('-')[0]
                bottlenecks['blocked_status'].append(issue_data)
        
        # Get project names
        project_info = []
        for key in project_keys:
            project = Config.get_project_by_key(key)
            if project:
                project_info.append({
                    'key': key,
                    'name': project.get('name', key),
                    'issue_count': len(issues_by_project.get(key, []))
                })
        
        return {
            'generated_at': datetime.now().isoformat(),
            'aggregate_mode': True,
            'projects': project_info,
            'team_members': team_members,
            'team_stats': team_stats,
            'issues_by_status': dict(issues_by_status),
            'issues_by_project': dict(issues_by_project),
            'total_team_issues': len(team_issues),
            'bottlenecks': bottlenecks,
            'summary': {
                'total_members': len(team_members),
                'total_issues': len(team_issues),
                'total_projects': len(project_keys),
                'status_breakdown': {status: len(issues) for status, issues in issues_by_status.items()},
                'project_breakdown': {key: len(issues) for key, issues in issues_by_project.items()},
                'avg_workload': len(team_issues) / len(team_members) if team_members else 0,
                'total_stale': len(bottlenecks['stale_issues']),
                'total_aging': len(bottlenecks['aging_in_progress']),
                'total_at_risk': len(bottlenecks['high_priority_at_risk']),
                'total_overloaded': len(bottlenecks['workload_imbalance'])
            }
        }
    
    def generate_historical_report(self, period: str = 'last_week', project_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a historical activity report for a specific period.
        
        Args:
            period: 'last_week', 'last_month', 'current_week', 'current_month'
            project_keys: Optional list of project keys. If None, checks config for aggregate mode.
            
        Returns:
            Dictionary containing historical report data
        """
        from ..config import Config
        
        # If no project_keys specified, check if we should use aggregate mode
        if project_keys is None:
            Config.load_config_file()
            projects = Config.get_projects()
            
            # If aggregate mode is enabled and multiple projects exist, use all
            if Config.is_aggregate_mode() and len(projects) > 1:
                project_keys = [p['key'] for p in projects]
            elif len(projects) == 1:
                # Single project from config
                project_keys = [projects[0]['key']]
            # else: project_keys stays None, will use JiraClient's default project_key
        
        start_date, end_date = self.get_date_range(period)
        
        # Get issues in various states during this period
        if project_keys and len(project_keys) > 1:
            # Multi-project mode
            completed_issues = self.jira.get_multi_project_completed_in_period(project_keys, start_date, end_date)
            updated_issues = self.jira.get_multi_project_updated_in_period(project_keys, start_date, end_date)
            created_issues = self.jira.get_multi_project_created_in_period(project_keys, start_date, end_date)
        else:
            # Single project mode
            completed_issues = self.jira.get_issues_completed_in_period(start_date, end_date)
            updated_issues = self.jira.get_issues_updated_in_period(start_date, end_date)
            created_issues = self.jira.get_issues_created_in_period(start_date, end_date)
        
        # Organize by assignee
        completed_by_assignee = defaultdict(list)
        updated_by_assignee = defaultdict(list)
        created_by_assignee = defaultdict(list)
        
        for issue in completed_issues:
            issue_data = self.jira.format_issue(issue)
            completed_by_assignee[issue_data['assignee']].append(issue_data)
        
        for issue in updated_issues:
            issue_data = self.jira.format_issue(issue)
            updated_by_assignee[issue_data['assignee']].append(issue_data)
        
        for issue in created_issues:
            issue_data = self.jira.format_issue(issue)
            created_by_assignee[issue_data['reporter']].append(issue_data)
        
        # Calculate team productivity metrics
        team_metrics = {}
        all_assignees = set(list(completed_by_assignee.keys()) + 
                          list(updated_by_assignee.keys()) + 
                          list(created_by_assignee.keys()))
        
        for assignee in all_assignees:
            if assignee and assignee != 'Unassigned':
                team_metrics[assignee] = {
                    'completed': len(completed_by_assignee.get(assignee, [])),
                    'updated': len(updated_by_assignee.get(assignee, [])),
                    'created': len(created_by_assignee.get(assignee, [])),
                    'completed_issues': completed_by_assignee.get(assignee, []),
                    'updated_issues': updated_by_assignee.get(assignee, [])[:10],  # Limit to 10 for display
                }
        
        return {
            'period': period,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'completed_issues': [self.jira.format_issue(i) for i in completed_issues],
            'created_issues': [self.jira.format_issue(i) for i in created_issues],
            'team_metrics': team_metrics,
            'summary': {
                'total_completed': len(completed_issues),
                'total_updated': len(updated_issues),
                'total_created': len(created_issues),
                'active_team_members': len(team_metrics)
            }
        }
    
    def format_team_report_as_text(self, report: Dict[str, Any]) -> str:
        """
        Format team report as readable text.
        
        Args:
            report: Team report dictionary
            
        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("👥 TEAM ACTIVITY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("📊 TEAM SUMMARY")
        lines.append("-" * 80)
        summary = report['summary']
        lines.append(f"  • Team Members: {summary['total_members']}")
        lines.append(f"  • Total Active Issues: {summary['total_issues']}")
        lines.append("")
        lines.append("  Status Breakdown:")
        for status, count in summary['status_breakdown'].items():
            lines.append(f"    - {status}: {count}")
        lines.append("")
        
        # Team member details
        lines.append("👤 TEAM MEMBER DETAILS")
        lines.append("-" * 80)
        
        for member_name, stats in sorted(report['team_stats'].items()):
            if stats['total_issues'] > 0:
                lines.append(f"\n{member_name}")
                lines.append(f"  Total Issues: {stats['total_issues']}")
                lines.append(f"  By Status:")
                for status, count in stats['by_status'].items():
                    lines.append(f"    - {status}: {count}")
                lines.append(f"  By Priority:")
                for priority, count in stats['by_priority'].items():
                    lines.append(f"    - {priority}: {count}")
                
                # Show top 5 issues
                if stats['issues']:
                    lines.append(f"  Top Issues:")
                    for issue in stats['issues'][:5]:
                        lines.append(f"    - [{issue['key']}] {issue['summary']} ({issue['status']})")
                lines.append("")
        
        # Bottleneck Detection
        bottlenecks = report.get('bottlenecks', {})
        if bottlenecks:
            lines.append("⚠️  BOTTLENECK DETECTION & RISK ANALYSIS")
            lines.append("-" * 80)
            lines.append("")
            
            # Alert summary
            lines.append(f"  🕐 Stale Issues (7+ days): {summary.get('total_stale', 0)}")
            lines.append(f"  ⏳ Aging In Progress (14+ days): {summary.get('total_aging', 0)}")
            lines.append(f"  🎯 High Priority At Risk: {summary.get('total_at_risk', 0)}")
            lines.append(f"  📊 Workload Imbalance: {summary.get('total_overloaded', 0)} overloaded members")
            lines.append("")
            
            if bottlenecks.get('stale_issues'):
                lines.append("  🕐 Stale Issues:")
                for issue in sorted(bottlenecks['stale_issues'], key=lambda x: x['days_since_update'], reverse=True)[:5]:
                    lines.append(f"    - [{issue['key']}] {issue['summary'][:60]}")
                    lines.append(f"      {issue['days_since_update']} days stale | Assignee: {issue['assignee']}")
                lines.append("")
            
            if bottlenecks.get('aging_in_progress'):
                lines.append("  ⏳ Aging Work In Progress:")
                for issue in sorted(bottlenecks['aging_in_progress'], key=lambda x: x['days_since_update'], reverse=True)[:5]:
                    lines.append(f"    - [{issue['key']}] {issue['summary'][:60]}")
                    lines.append(f"      {issue['days_since_update']} days in progress | Assignee: {issue['assignee']}")
                lines.append("")
            
            if bottlenecks.get('high_priority_at_risk'):
                lines.append("  🎯 High Priority Items At Risk:")
                for issue in bottlenecks['high_priority_at_risk'][:5]:
                    lines.append(f"    - [{issue['key']}] {issue['summary'][:60]}")
                    lines.append(f"      {issue['days_since_creation']} days old | Priority: {issue['priority']}")
                lines.append("")
            
            if bottlenecks.get('workload_imbalance'):
                lines.append("  📊 Overloaded Team Members:")
                for item in bottlenecks['workload_imbalance']:
                    lines.append(f"    - {item['assignee']}: {item['total_issues']} issues (+{item['overload_percentage']:.0f}% above avg)")
                lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"Generated at: {report['generated_at']}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def format_historical_report_as_text(self, report: Dict[str, Any]) -> str:
        """
        Format historical report as readable text.
        
        Args:
            report: Historical report dictionary
            
        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"📈 HISTORICAL ACTIVITY REPORT - {report['period'].upper().replace('_', ' ')}")
        lines.append(f"Period: {report['start_date']} to {report['end_date']}")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("📊 ACTIVITY SUMMARY")
        lines.append("-" * 80)
        summary = report['summary']
        lines.append(f"  • Issues Completed: {summary['total_completed']}")
        lines.append(f"  • Issues Updated: {summary['total_updated']}")
        lines.append(f"  • Issues Created: {summary['total_created']}")
        lines.append(f"  • Active Team Members: {summary['active_team_members']}")
        lines.append("")
        
        # Team productivity
        lines.append("👥 TEAM PRODUCTIVITY")
        lines.append("-" * 80)
        
        for member_name, metrics in sorted(report['team_metrics'].items(), 
                                          key=lambda x: x[1]['completed'], 
                                          reverse=True):
            lines.append(f"\n{member_name}")
            lines.append(f"  ✅ Completed: {metrics['completed']}")
            lines.append(f"  🔄 Updated: {metrics['updated']}")
            lines.append(f"  ➕ Created: {metrics['created']}")
            
            if metrics['completed_issues']:
                lines.append(f"  Completed Issues:")
                for issue in metrics['completed_issues'][:5]:
                    lines.append(f"    - [{issue['key']}] {issue['summary']}")
            lines.append("")
        
        # All completed issues
        if report['completed_issues']:
            lines.append("✅ ALL COMPLETED ISSUES")
            lines.append("-" * 80)
            for issue in report['completed_issues'][:20]:  # Limit to 20
                lines.append(f"  [{issue['key']}] {issue['summary']}")
                lines.append(f"    Assignee: {issue['assignee']} | Priority: {issue['priority']}")
                lines.append(f"    {issue['url']}")
                lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"Generated at: {report['generated_at']}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _create_progress_bar(self, value: int, total: int, width: int = 20) -> str:
        """Create a visual progress bar."""
        if total == 0:
            return "░" * width
        filled = int((value / total) * width)
        return "█" * filled + "░" * (width - filled)
    
    def _get_priority_badge(self, priority: str) -> str:
        """Get emoji badge for priority."""
        badges = {
            'Highest': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢',
            'Lowest': '⚪'
        }
        return badges.get(priority, '⚫')
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        status_lower = status.lower()
        if 'progress' in status_lower:
            return '🔄'
        elif 'done' in status_lower or 'closed' in status_lower:
            return '✅'
        elif 'review' in status_lower:
            return '👀'
        elif 'blocked' in status_lower:
            return '🚫'
        else:
            return '📋'
    
    def format_team_report_as_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format team report as enhanced Markdown optimized for Agent consumption.
        
        Args:
            report: Team report dictionary
            
        Returns:
            Formatted Markdown string with structured metadata and actionable insights
        """
        lines = []
        summary = report['summary']
        
        # Structured Metadata Section for Agent Parsing
        lines.append("# 👥 Team Activity Report")
        lines.append("")
        lines.append("## 📋 Report Metadata")
        lines.append("")
        lines.append("```yaml")
        lines.append("report_type: team_activity")
        lines.append(f"generated_at: {report['generated_at']}")
        lines.append(f"total_members: {summary['total_members']}")
        lines.append(f"total_issues: {summary['total_issues']}")
        lines.append(f"avg_workload: {summary['total_issues'] / max(summary['total_members'], 1):.1f}")
        if report.get('aggregate_mode'):
            lines.append("mode: multi_project_aggregate")
            lines.append(f"project_count: {summary.get('total_projects', 0)}")
        else:
            lines.append("mode: single_project")
        lines.append("alert_counts:")
        lines.append(f"  stale_issues: {summary.get('total_stale', 0)}")
        lines.append(f"  aging_in_progress: {summary.get('total_aging', 0)}")
        lines.append(f"  high_priority_at_risk: {summary.get('total_at_risk', 0)}")
        lines.append(f"  overloaded_members: {summary.get('total_overloaded', 0)}")
        lines.append("```")
        lines.append("")
        
        # Show project info if aggregate mode
        if report.get('aggregate_mode'):
            lines.append("### 📦 Projects Included")
            lines.append("")
            lines.append("| Project | Key | Issues |")
            lines.append("|---------|-----|--------|")
            for proj in report.get('projects', []):
                lines.append(f"| {proj['name']} | `{proj['key']}` | {proj['issue_count']} |")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Actionable Insights Section
        bottlenecks = report.get('bottlenecks', {})
        lines.append("## 🎯 Key Insights & Recommended Actions")
        lines.append("")
        
        # Generate actionable recommendations
        recommendations = []
        if summary.get('total_stale', 0) > 0:
            recommendations.append(f"- **{summary['total_stale']} stale issues** need attention - Review and update or close")
        if summary.get('total_aging', 0) > 0:
            recommendations.append(f"- **{summary['total_aging']} issues** have been in progress for 14+ days - Check for blockers")
        if summary.get('total_at_risk', 0) > 0:
            recommendations.append(f"- **{summary['total_at_risk']} high-priority items** are aging - Prioritize or escalate")
        if summary.get('total_overloaded', 0) > 0:
            recommendations.append(f"- **{summary['total_overloaded']} team members** are overloaded - Consider redistributing work")
        
        if recommendations:
            for rec in recommendations:
                lines.append(rec)
        else:
            lines.append("- ✅ No critical issues detected - Team workflow is healthy")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Summary Cards
        lines.append("## 📊 Executive Summary")
        lines.append("")
        lines.append("| Metric | Value | ")
        lines.append("|--------|-------|")
        lines.append(f"| 👥 **Team Members** | {summary['total_members']} |")
        lines.append(f"| 📋 **Total Active Issues** | {summary['total_issues']} |")
        
        if report.get('aggregate_mode'):
            lines.append(f"| 🗂️ **Projects** | {summary.get('total_projects', 0)} |")
        
        lines.append(f"| 📈 **Avg Issues per Member** | {summary['total_issues'] / max(summary['total_members'], 1):.1f} |")
        lines.append("")
        
        # Status Distribution
        lines.append("### 📌 Status Distribution")
        lines.append("")
        lines.append("| Status | Count | Percentage | Progress |")
        lines.append("|--------|-------|------------|----------|")
        
        for status, count in sorted(summary['status_breakdown'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / summary['total_issues'] * 100) if summary['total_issues'] > 0 else 0
            progress_bar = self._create_progress_bar(count, summary['total_issues'], 15)
            emoji = self._get_status_emoji(status)
            lines.append(f"| {emoji} {status} | {count} | {percentage:.1f}% | `{progress_bar}` |")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Team Performance Overview Table
        lines.append("## 🎯 Team Performance Overview")
        lines.append("")
        lines.append("| Team Member | Total Issues | In Progress | To Do | In Review | Completed |")
        lines.append("|-------------|--------------|-------------|-------|-----------|-----------|")
        
        for member_name, stats in sorted(report['team_stats'].items(), key=lambda x: x[1]['total_issues'], reverse=True):
            if stats['total_issues'] > 0:
                in_progress = stats['by_status'].get('In Progress', 0)
                to_do = stats['by_status'].get('To Do', 0)
                in_review = stats['by_status'].get('In Review', 0) + stats['by_status'].get('Code Review', 0)
                completed = stats['by_status'].get('Done', 0) + stats['by_status'].get('Closed', 0)
                
                lines.append(f"| **{member_name}** | {stats['total_issues']} | {in_progress} | {to_do} | {in_review} | {completed} |")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Detailed Team Member Breakdown
        lines.append("## 👤 Detailed Team Member Breakdown")
        lines.append("")
        
        for member_name, stats in sorted(report['team_stats'].items(), key=lambda x: x[1]['total_issues'], reverse=True):
            if stats['total_issues'] > 0:
                lines.append(f"### {member_name}")
                lines.append("")
                
                # Member stats card
                lines.append("| Metric | Value |")
                lines.append("|--------|-------|")
                lines.append(f"| 📋 **Total Issues** | {stats['total_issues']} |")
                
                # Status breakdown
                if stats['by_status']:
                    for status, count in sorted(stats['by_status'].items(), key=lambda x: x[1], reverse=True):
                        emoji = self._get_status_emoji(status)
                        lines.append(f"| {emoji} {status} | {count} |")
                
                lines.append("")
                
                # Priority distribution
                if stats['by_priority']:
                    lines.append("**Priority Distribution:**")
                    lines.append("")
                    for priority, count in sorted(stats['by_priority'].items(), key=lambda x: x[1], reverse=True):
                        badge = self._get_priority_badge(priority)
                        progress = self._create_progress_bar(count, stats['total_issues'], 10)
                        lines.append(f"- {badge} **{priority}**: {count} `{progress}`")
                    lines.append("")
                
                # Top issues
                if stats['issues']:
                    lines.append("<details>")
                    lines.append(f"<summary><b>🔍 View Top {min(5, len(stats['issues']))} Issues</b></summary>")
                    lines.append("")
                    lines.append("| Issue | Summary | Status | Priority |")
                    lines.append("|-------|---------|--------|----------|")
                    
                    for issue in stats['issues'][:5]:
                        status_emoji = self._get_status_emoji(issue['status'])
                        priority_badge = self._get_priority_badge(issue['priority'])
                        lines.append(f"| [{issue['key']}]({issue['url']}) | {issue['summary'][:50]}... | {status_emoji} {issue['status']} | {priority_badge} {issue['priority']} |")
                    
                    lines.append("")
                    lines.append("</details>")
                    lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Bottleneck Detection Section
        lines.append("## ⚠️ Bottleneck Detection & Risk Analysis")
        lines.append("")
        lines.append("*This section identifies potential workflow blockers and risks that need attention.*")
        lines.append("")
        
        # Summary metrics
        lines.append("### 📊 Alert Summary")
        lines.append("")
        lines.append("| Alert Type | Count | Severity |")
        lines.append("|------------|-------|----------|")
        lines.append(f"| 🕐 **Stale Issues** (No update in 7+ days) | {summary.get('total_stale', 0)} | {'🔴 High' if summary.get('total_stale', 0) > 5 else '🟡 Medium' if summary.get('total_stale', 0) > 0 else '🟢 Low'} |")
        lines.append(f"| ⏳ **Aging In Progress** (14+ days) | {summary.get('total_aging', 0)} | {'🔴 High' if summary.get('total_aging', 0) > 3 else '🟡 Medium' if summary.get('total_aging', 0) > 0 else '🟢 Low'} |")
        lines.append(f"| 🎯 **High Priority At Risk** (14+ days old) | {summary.get('total_at_risk', 0)} | {'🔴 High' if summary.get('total_at_risk', 0) > 0 else '🟢 Low'} |")
        lines.append(f"| 📊 **Workload Imbalance** | {summary.get('total_overloaded', 0)} | {'🟠 Medium' if summary.get('total_overloaded', 0) > 0 else '🟢 Low'} |")
        lines.append("")
        
        # Stale Issues
        if bottlenecks.get('stale_issues'):
            lines.append("### 🕐 Stale Issues (No Updates in 7+ Days)")
            lines.append("")
            lines.append("These issues haven't been updated recently and may be blocked or forgotten:")
            lines.append("")
            lines.append("| Issue | Summary | Assignee | Status | ⏱️ Days Stale | Priority |")
            lines.append("|-------|---------|----------|--------|---------------|----------|")
            
            for issue in sorted(bottlenecks['stale_issues'], key=lambda x: x['days_since_update'], reverse=True)[:10]:
                badge = self._get_priority_badge(issue['priority'])
                emoji = self._get_status_emoji(issue['status'])
                lines.append(f"| [{issue['key']}]({issue['url']}) | {issue['summary'][:40]}... | {issue['assignee']} | {emoji} {issue['status']} | **{issue['days_since_update']}** | {badge} {issue['priority']} |")
            
            lines.append("")
        
        # Aging In Progress
        if bottlenecks.get('aging_in_progress'):
            lines.append("### ⏳ Aging Work In Progress")
            lines.append("")
            lines.append("Issues that have been in progress for more than 14 days:")
            lines.append("")
            lines.append("| Issue | Summary | Assignee | ⏱️ Days In Progress | Priority |")
            lines.append("|-------|---------|----------|---------------------|----------|")
            
            for issue in sorted(bottlenecks['aging_in_progress'], key=lambda x: x['days_since_update'], reverse=True):
                badge = self._get_priority_badge(issue['priority'])
                lines.append(f"| [{issue['key']}]({issue['url']}) | {issue['summary'][:45]}... | {issue['assignee']} | **{issue['days_since_update']}** | {badge} {issue['priority']} |")
            
            lines.append("")
        
        # High Priority At Risk
        if bottlenecks.get('high_priority_at_risk'):
            lines.append("### 🎯 High Priority Items At Risk")
            lines.append("")
            lines.append("Critical/High priority issues that are taking too long (14+ days):")
            lines.append("")
            lines.append("| Issue | Summary | Assignee | Status | ⏱️ Age (days) | Priority |")
            lines.append("|-------|---------|----------|--------|---------------|----------|")
            
            for issue in sorted(bottlenecks['high_priority_at_risk'], key=lambda x: x['days_since_creation'], reverse=True):
                badge = self._get_priority_badge(issue['priority'])
                emoji = self._get_status_emoji(issue['status'])
                lines.append(f"| [{issue['key']}]({issue['url']}) | {issue['summary'][:40]}... | {issue['assignee']} | {emoji} {issue['status']} | **{issue['days_since_creation']}** | {badge} {issue['priority']} |")
            
            lines.append("")
        
        # Workload Imbalance
        if bottlenecks.get('workload_imbalance'):
            lines.append("### 📊 Workload Distribution Analysis")
            lines.append("")
            lines.append(f"Average workload: **{summary.get('avg_workload', 0):.1f} issues per person**")
            lines.append("")
            lines.append("Team members with significantly higher workload (50%+ above average):")
            lines.append("")
            lines.append("| Team Member | Issues | Average | Overload % | Status |")
            lines.append("|-------------|--------|---------|------------|--------|")
            
            for item in sorted(bottlenecks['workload_imbalance'], key=lambda x: x['overload_percentage'], reverse=True):
                lines.append(f"| **{item['assignee']}** | {item['total_issues']} | {item['average']:.1f} | **+{item['overload_percentage']:.1f}%** | ⚠️ Overloaded |")
            
            lines.append("")
        
        # Blocked Issues
        if bottlenecks.get('blocked_status'):
            lines.append("### 🚫 Blocked Issues")
            lines.append("")
            lines.append("Issues currently marked as blocked:")
            lines.append("")
            lines.append("| Issue | Summary | Assignee | Days Blocked | Priority |")
            lines.append("|-------|---------|----------|--------------|----------|")
            
            for issue in bottlenecks['blocked_status']:
                badge = self._get_priority_badge(issue['priority'])
                lines.append(f"| [{issue['key']}]({issue['url']}) | {issue['summary'][:45]}... | {issue['assignee']} | {issue['days_since_update']} | {badge} {issue['priority']} |")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # LLM-Optimized Recap Section
        lines.append("## 🤖 AI-Ready Executive Summary")
        lines.append("")
        lines.append("_This section is structured for LLM consumption and decision support._")
        lines.append("")
        lines.append("```")
        lines.append("=== PROJECT HEALTH SNAPSHOT ===")
        lines.append("")
        lines.append(f"Team Size: {summary.get('total_members', 0)} members")
        lines.append(f"Total Active Issues: {summary.get('total_issues', 0)}")
        lines.append(f"Average Workload: {summary.get('avg_workload', 0):.1f} issues per person")
        lines.append("")
        
        # Status breakdown
        lines.append("Status Distribution:")
        for status, count in sorted(summary.get('status_breakdown', {}).items(), key=lambda x: x[1], reverse=True):
            percentage = (count / summary['total_issues'] * 100) if summary['total_issues'] > 0 else 0
            lines.append(f"  - {status}: {count} ({percentage:.1f}%)")
        lines.append("")
        
        # Critical issues
        lines.append("=== CRITICAL ALERTS ===")
        lines.append("")
        
        total_alerts = (summary.get('total_stale', 0) + 
                       summary.get('total_aging', 0) + 
                       summary.get('total_at_risk', 0) +
                       summary.get('total_overloaded', 0))
        
        if total_alerts > 0:
            lines.append(f"⚠️  {total_alerts} active bottlenecks detected")
            lines.append("")
            
            if summary.get('total_stale', 0) > 0:
                lines.append(f"1. STALE ISSUES: {summary.get('total_stale')} issues have no updates in 7+ days")
                if bottlenecks.get('stale_issues'):
                    lines.append("   Most stale:")
                    for issue in sorted(bottlenecks['stale_issues'], key=lambda x: x['days_since_update'], reverse=True)[:3]:
                        lines.append(f"   - {issue['key']}: {issue['summary'][:60]} ({issue['days_since_update']} days)")
                lines.append("")
            
            if summary.get('total_aging', 0) > 0:
                lines.append(f"2. AGING WORK: {summary.get('total_aging')} issues in progress for 14+ days")
                if bottlenecks.get('aging_in_progress'):
                    lines.append("   Longest running:")
                    for issue in sorted(bottlenecks['aging_in_progress'], key=lambda x: x['days_since_update'], reverse=True)[:3]:
                        lines.append(f"   - {issue['key']}: {issue['summary'][:60]} ({issue['days_since_update']} days)")
                lines.append("")
            
            if summary.get('total_at_risk', 0) > 0:
                lines.append(f"3. HIGH PRIORITY RISK: {summary.get('total_at_risk')} critical items open for 14+ days")
                if bottlenecks.get('high_priority_at_risk'):
                    lines.append("   At-risk items:")
                    for issue in sorted(bottlenecks['high_priority_at_risk'], key=lambda x: x['days_since_creation'], reverse=True)[:3]:
                        lines.append(f"   - {issue['key']}: {issue['summary'][:60]} ({issue['days_since_creation']} days old)")
                lines.append("")
            
            if summary.get('total_overloaded', 0) > 0:
                lines.append(f"4. WORKLOAD IMBALANCE: {summary.get('total_overloaded')} team members overloaded")
                if bottlenecks.get('workload_imbalance'):
                    lines.append("   Overloaded members:")
                    for item in sorted(bottlenecks['workload_imbalance'], key=lambda x: x['overload_percentage'], reverse=True):
                        lines.append(f"   - {item['assignee']}: {item['total_issues']} issues (+{item['overload_percentage']:.0f}% above average)")
                lines.append("")
        else:
            lines.append("✅ No critical bottlenecks detected")
            lines.append("")
        
        # Recommendations
        lines.append("=== RECOMMENDED ACTIONS ===")
        lines.append("")
        
        if total_alerts > 0:
            action_count = 1
            
            if summary.get('total_stale', 0) > 5:
                lines.append(f"{action_count}. Review and update stale issues or close if no longer relevant")
                action_count += 1
            
            if summary.get('total_aging', 0) > 3:
                lines.append(f"{action_count}. Investigate blockers for long-running in-progress items")
                action_count += 1
            
            if summary.get('total_at_risk', 0) > 0:
                lines.append(f"{action_count}. Prioritize high-priority items that are aging")
                action_count += 1
            
            if summary.get('total_overloaded', 0) > 0:
                lines.append(f"{action_count}. Redistribute work from overloaded team members")
                action_count += 1
            
            if bottlenecks.get('blocked_status'):
                lines.append(f"{action_count}. Resolve blockers for {len(bottlenecks['blocked_status'])} blocked issues")
                action_count += 1
        else:
            lines.append("- Continue monitoring workflow health")
            lines.append("- Maintain current team velocity")
        
        lines.append("")
        lines.append("=== TEAM PERFORMANCE SUMMARY ===")
        lines.append("")
        
        # Top performers
        top_performers = sorted(report['team_stats'].items(), key=lambda x: x[1]['total_issues'], reverse=True)[:3]
        lines.append("Most Active Members:")
        for i, (name, stats) in enumerate(top_performers, 1):
            if stats['total_issues'] > 0:
                lines.append(f"{i}. {name}: {stats['total_issues']} active issues")
        
        lines.append("")
        lines.append("```")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("<div align='center'>")
        lines.append(f"<sub>📅 Generated at {report['generated_at'][:19].replace('T', ' at ')} | 🤖 Abulafia Bot</sub>")
        lines.append("</div>")
        
        return "\n".join(lines)
    
    def format_historical_report_as_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format historical report as enhanced Markdown with charts and visual elements.
        
        Args:
            report: Historical report dictionary
            
        Returns:
            Formatted Markdown string
        """
        lines = []
        summary = report['summary']
        period_name = report['period'].replace('_', ' ').title()
        
        # Header with timeline
        lines.append(f"# 📈 Historical Activity Report")
        lines.append("")
        lines.append(f"## {period_name}")
        lines.append("")
        lines.append(f"> 📅 **Period:** {report['start_date']} to {report['end_date']}  ")
        lines.append(f"> ⏰ **Generated:** {report['generated_at'][:19].replace('T', ' at ')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Key Metrics Dashboard
        lines.append("## 📊 Key Metrics Dashboard")
        lines.append("")
        lines.append("<table>")
        lines.append("<tr>")
        lines.append(f'<td align="center"><h3>✅<br/>{summary["total_completed"]}</h3><sub>Completed</sub></td>')
        lines.append(f'<td align="center"><h3>🔄<br/>{summary["total_updated"]}</h3><sub>Updated</sub></td>')
        lines.append(f'<td align="center"><h3>➕<br/>{summary["total_created"]}</h3><sub>Created</sub></td>')
        lines.append(f'<td align="center"><h3>👥<br/>{summary["active_team_members"]}</h3><sub>Active Members</sub></td>')
        lines.append("</tr>")
        lines.append("</table>")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Team Productivity Leaderboard
        lines.append("## 🏆 Team Productivity Leaderboard")
        lines.append("")
        lines.append("| Rank | Team Member | ✅ Completed | 🔄 Updated | ➕ Created | 🎯 Total Activity |")
        lines.append("|------|-------------|--------------|------------|-----------|------------------|")
        
        sorted_members = sorted(report['team_metrics'].items(), 
                               key=lambda x: x[1]['completed'], 
                               reverse=True)
        
        for rank, (member_name, metrics) in enumerate(sorted_members, 1):
            total_activity = metrics['completed'] + metrics['updated'] + metrics['created']
            medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'{rank}.'
            lines.append(f"| {medal} | **{member_name}** | {metrics['completed']} | {metrics['updated']} | {metrics['created']} | **{total_activity}** |")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Detailed Team Member Contributions
        lines.append("## 👥 Detailed Team Contributions")
        lines.append("")
        
        for member_name, metrics in sorted_members:
            lines.append(f"### {member_name}")
            lines.append("")
            
            # Activity summary
            total_activity = metrics['completed'] + metrics['updated'] + metrics['created']
            if total_activity > 0:
                completed_pct = (metrics['completed'] / total_activity * 100)
                lines.append("**Activity Breakdown:**")
                lines.append("")
                lines.append(f"- ✅ Completed: `{metrics['completed']}` {self._create_progress_bar(metrics['completed'], total_activity, 15)} {completed_pct:.1f}%")
                lines.append(f"- 🔄 Updated: `{metrics['updated']}` {self._create_progress_bar(metrics['updated'], total_activity, 15)} {(metrics['updated'] / total_activity * 100):.1f}%")
                lines.append(f"- ➕ Created: `{metrics['created']}` {self._create_progress_bar(metrics['created'], total_activity, 15)} {(metrics['created'] / total_activity * 100):.1f}%")
                lines.append("")
            
            # Completed issues details
            if metrics.get('completed_issues'):
                lines.append("<details>")
                lines.append(f"<summary><b>✅ View Completed Issues ({len(metrics['completed_issues'])})</b></summary>")
                lines.append("")
                lines.append("| Issue | Summary | Priority |")
                lines.append("|-------|---------|----------|")
                
                for issue in metrics['completed_issues'][:10]:
                    priority_badge = self._get_priority_badge(issue['priority'])
                    summary_text = issue['summary'][:60] + '...' if len(issue['summary']) > 60 else issue['summary']
                    lines.append(f"| [{issue['key']}]({issue['url']}) | {summary_text} | {priority_badge} {issue['priority']} |")
                
                lines.append("")
                lines.append("</details>")
                lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # All Completed Issues Section
        if report['completed_issues']:
            lines.append("## ✅ All Completed Issues")
            lines.append("")
            lines.append(f"_Showing {min(20, len(report['completed_issues']))} of {len(report['completed_issues'])} completed issues_")
            lines.append("")
            
            lines.append("<details>")
            lines.append("<summary><b>📋 Expand to see all completed issues</b></summary>")
            lines.append("")
            lines.append("| Issue | Summary | Assignee | Priority |")
            lines.append("|-------|---------|----------|----------|")
            
            for issue in report['completed_issues'][:20]:
                priority_badge = self._get_priority_badge(issue['priority'])
                summary_text = issue['summary'][:50] + '...' if len(issue['summary']) > 50 else issue['summary']
                lines.append(f"| [{issue['key']}]({issue['url']}) | {summary_text} | {issue['assignee']} | {priority_badge} {issue['priority']} |")
            
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("<div align='center'>")
        lines.append(f"<sub>📈 Historical Report | Period: {report['start_date']} - {report['end_date']} | 🤖 Abulafia Bot</sub>")
        lines.append("</div>")
        
        return "\n".join(lines)
    
    def format_team_report_as_marp(self, report: Dict[str, Any]) -> str:
        """
        Format team report as Marp presentation.
        
        Args:
            report: Team report dictionary
            
        Returns:
            Formatted Marp markdown string
        """
        lines = []
        summary = report['summary']
        
        # Marp frontmatter
        lines.append("---")
        lines.append("marp: true")
        lines.append("theme: default")
        lines.append("paginate: true")
        lines.append("header: '👥 Team Activity Report'")
        lines.append(f"footer: 'Generated: {report['generated_at'][:10]}'")
        lines.append("---")
        lines.append("")
        
        # Title slide
        lines.append("<!-- _class: lead -->")
        lines.append("")
        lines.append("# 👥 Team Activity Report")
        lines.append("")
        if report.get('aggregate_mode'):
            lines.append("## Multi-Project Aggregate")
            lines.append(f"### {summary.get('total_projects', 0)} Projects")
        lines.append(f"## {summary['total_members']} Team Members")
        lines.append(f"## {summary['total_issues']} Active Issues")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Projects slide (if aggregate)
        if report.get('aggregate_mode') and report.get('projects'):
            lines.append("# 📦 Projects")
            lines.append("")
            for proj in report['projects']:
                lines.append(f"## {proj['name']} (`{proj['key']}`)")
                lines.append(f"**{proj['issue_count']} issues**")
                lines.append("")
            lines.append("---")
            lines.append("")
        
        # Summary slide
        lines.append("# 📊 Overview")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| 👥 Team Members | {summary['total_members']} |")
        lines.append(f"| 📋 Total Issues | {summary['total_issues']} |")
        if report.get('aggregate_mode'):
            lines.append(f"| 🗂️ Projects | {summary.get('total_projects', 0)} |")
        lines.append(f"| 📈 Avg per Member | {summary['total_issues'] / max(summary['total_members'], 1):.1f} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Status Distribution
        lines.append("# 📌 Status Distribution")
        lines.append("")
        for status, count in sorted(summary['status_breakdown'].items(), key=lambda x: x[1], reverse=True)[:6]:
            percentage = (count / summary['total_issues'] * 100) if summary['total_issues'] > 0 else 0
            emoji = self._get_status_emoji(status)
            lines.append(f"### {emoji} {status}")
            lines.append(f"**{count} issues** ({percentage:.1f}%)")
            lines.append("")
        lines.append("---")
        lines.append("")
        
        # Bottleneck Alerts
        bottlenecks = report.get('bottlenecks', {})
        total_alerts = (summary.get('total_stale', 0) + 
                       summary.get('total_aging', 0) + 
                       summary.get('total_at_risk', 0) +
                       summary.get('total_overloaded', 0))
        
        if total_alerts > 0:
            lines.append("# ⚠️ Bottleneck Alerts")
            lines.append("")
            
            if summary.get('total_stale', 0) > 0:
                severity = '🔴' if summary['total_stale'] > 5 else '🟡'
                lines.append(f"### {severity} Stale Issues")
                lines.append(f"**{summary['total_stale']} issues** with no updates in 7+ days")
                lines.append("")
            
            if summary.get('total_aging', 0) > 0:
                severity = '🔴' if summary['total_aging'] > 3 else '🟡'
                lines.append(f"### {severity} Aging Work")
                lines.append(f"**{summary['total_aging']} issues** in progress for 14+ days")
                lines.append("")
            
            if summary.get('total_at_risk', 0) > 0:
                lines.append(f"### 🔴 High Priority at Risk")
                lines.append(f"**{summary['total_at_risk']} critical items** taking too long")
                lines.append("")
            
            if summary.get('total_overloaded', 0) > 0:
                lines.append(f"### 🟠 Workload Imbalance")
                lines.append(f"**{summary['total_overloaded']} team members** overloaded")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Top stale issues
        if bottlenecks.get('stale_issues'):
            lines.append("# 🕐 Most Stale Issues")
            lines.append("")
            for issue in sorted(bottlenecks['stale_issues'], key=lambda x: x['days_since_update'], reverse=True)[:5]:
                badge = self._get_priority_badge(issue['priority'])
                lines.append(f"### {badge} [{issue['key']}]({issue['url']})")
                lines.append(f"**{issue['summary'][:60]}**")
                lines.append(f"⏱️ {issue['days_since_update']} days | Assignee: {issue['assignee']}")
                lines.append("")
            lines.append("---")
            lines.append("")
        
        # Team Performance
        lines.append("# 🎯 Top Performers")
        lines.append("")
        top_members = sorted(report['team_stats'].items(), key=lambda x: x[1]['total_issues'], reverse=True)[:5]
        for i, (name, stats) in enumerate(top_members, 1):
            if stats['total_issues'] > 0:
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}."
                lines.append(f"## {medal} {name}")
                lines.append(f"**{stats['total_issues']} active issues**")
                lines.append("")
        lines.append("---")
        lines.append("")
        
        # Recommendations
        lines.append("<!-- _class: lead -->")
        lines.append("")
        lines.append("# 💡 Recommendations")
        lines.append("")
        
        if total_alerts > 5:
            lines.append("## ⚠️ Immediate Action Needed")
            lines.append("")
            if summary.get('total_stale', 0) > 5:
                lines.append("- Review and update stale issues")
            if summary.get('total_aging', 0) > 3:
                lines.append("- Investigate blockers on aging work")
            if summary.get('total_at_risk', 0) > 0:
                lines.append("- Prioritize critical items")
            if summary.get('total_overloaded', 0) > 0:
                lines.append("- Redistribute workload")
        else:
            lines.append("## ✅ Team On Track")
            lines.append("")
            lines.append("Continue current pace and monitor")
        
        return "\n".join(lines)
    
    def format_historical_report_as_marp(self, report: Dict[str, Any]) -> str:
        """
        Format historical report as Marp presentation.
        
        Args:
            report: Historical report dictionary
            
        Returns:
            Formatted Marp markdown string
        """
        lines = []
        summary = report['summary']
        period_name = report['period'].replace('_', ' ').title()
        
        # Marp frontmatter
        lines.append("---")
        lines.append("marp: true")
        lines.append("theme: default")
        lines.append("paginate: true")
        lines.append("header: '📈 Historical Activity Report'")
        lines.append(f"footer: '{report['start_date']} to {report['end_date']}'")
        lines.append("---")
        lines.append("")
        
        # Title slide
        lines.append("<!-- _class: lead -->")
        lines.append("")
        lines.append("# 📈 Historical Activity Report")
        lines.append("")
        lines.append(f"## {period_name}")
        lines.append(f"### {report['start_date']} to {report['end_date']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Key Metrics
        lines.append("# 📊 Key Metrics")
        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| ✅ Completed | **{summary['total_completed']}** |")
        lines.append(f"| 🔄 Updated | {summary['total_updated']} |")
        lines.append(f"| ➕ Created | {summary['total_created']} |")
        lines.append(f"| 👥 Active Members | {summary['active_team_members']} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Team Leaderboard
        if report['team_metrics']:
            lines.append("# 🏆 Team Productivity")
            lines.append("")
            sorted_members = sorted(report['team_metrics'].items(), 
                                  key=lambda x: x[1]['completed'] + x[1]['updated'], 
                                  reverse=True)[:5]
            
            for i, (name, metrics) in enumerate(sorted_members, 1):
                medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f"{i}."
                total_activity = metrics['completed'] + metrics['updated']
                lines.append(f"## {medal} {name}")
                lines.append(f"✅ {metrics['completed']} completed | 🔄 {metrics['updated']} updated | ➕ {metrics['created']} created")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Top Completed Issues
        if report['completed_issues']:
            lines.append("# ✅ Completed Highlights")
            lines.append("")
            for issue in report['completed_issues'][:6]:
                badge = self._get_priority_badge(issue['priority'])
                lines.append(f"### {badge} [{issue['key']}]({issue['url']})")
                lines.append(f"**{issue['summary'][:60]}**")
                lines.append(f"_{issue['assignee']}*")
                lines.append("")
            lines.append("---")
            lines.append("")
        
        # Velocity Analysis
        lines.append("# 📈 Team Velocity")
        lines.append("")
        
        if summary['total_completed'] > 0:
            avg_per_member = summary['total_completed'] / summary['active_team_members'] if summary['active_team_members'] > 0 else 0
            lines.append(f"## {summary['total_completed']} Issues Completed")
            lines.append("")
            lines.append(f"### Average: {avg_per_member:.1f} per member")
            lines.append("")
            
            if avg_per_member > 5:
                lines.append("✅ **Excellent velocity!**")
            elif avg_per_member > 3:
                lines.append("👍 **Good pace**")
            else:
                lines.append("⚠️ **Below average - investigate blockers**")
        else:
            lines.append("⚠️ **No completed issues this period**")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Summary slide
        lines.append("<!-- _class: lead -->")
        lines.append("")
        lines.append("# 🎯 Period Summary")
        lines.append("")
        lines.append(f"## ✅ {summary['total_completed']} Completed")
        lines.append(f"## 🔄 {summary['total_updated']} Updated")
        lines.append(f"## ➕ {summary['total_created']} Created")
        lines.append("")
        lines.append("_Keep up the momentum! 🚀_")
        
        return "\n".join(lines)
