"""Weekly agenda generator from Jira issues."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..clients.jira_client import JiraClient


class AgendaGenerator:
    """Generate weekly agendas from Jira data."""
    
    def __init__(self, jira_client: JiraClient):
        """
        Initialize agenda generator.
        
        Args:
            jira_client: Instance of JiraClient
        """
        self.jira = jira_client
    
    def get_week_dates(self) -> tuple:
        """
        Get start and end dates of the current week.
        
        Returns:
            Tuple of (start_date, end_date)
        """
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return start_of_week, end_of_week
    
    def generate_weekly_agenda(self) -> Dict[str, Any]:
        """
        Generate a comprehensive weekly agenda from Jira data.
        
        Returns:
            Dictionary containing agenda data organized by categories
        """
        start_date, end_date = self.get_week_dates()
        
        # Fetch various issue categories
        assigned_issues = self.jira.get_assigned_issues()
        in_progress_issues = self.jira.get_issues_by_status("In Progress")
        due_this_week = self.jira.get_issues_due_this_week()
        recently_updated = self.jira.get_recently_updated_issues(days=7)
        
        # Get sprint issues if board is configured
        sprint_issues = []
        try:
            sprint_issues = self.jira.get_sprint_issues()
        except Exception:
            pass  # Board might not be configured
        
        # Format issues
        agenda = {
            'week_start': start_date.strftime('%Y-%m-%d'),
            'week_end': end_date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'in_progress': [self.jira.format_issue(issue) for issue in in_progress_issues],
            'due_this_week': [self.jira.format_issue(issue) for issue in due_this_week],
            'assigned_issues': [self.jira.format_issue(issue) for issue in assigned_issues[:10]],  # Top 10
            'sprint_issues': [self.jira.format_issue(issue) for issue in sprint_issues],
            'recently_updated': [self.jira.format_issue(issue) for issue in recently_updated[:10]],
        }
        
        # Add summary stats
        agenda['summary'] = {
            'total_assigned': len(assigned_issues),
            'in_progress_count': len(in_progress_issues),
            'due_this_week_count': len(due_this_week),
            'sprint_issues_count': len(sprint_issues),
            'recently_updated_count': len(recently_updated)
        }
        
        return agenda
    
    def format_agenda_as_text(self, agenda: Dict[str, Any]) -> str:
        """
        Format agenda dictionary as readable text.
        
        Args:
            agenda: Agenda dictionary from generate_weekly_agenda
            
        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"📅 WEEKLY AGENDA: {agenda['week_start']} to {agenda['week_end']}")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("📊 SUMMARY")
        lines.append("-" * 80)
        summary = agenda['summary']
        lines.append(f"  • Total Assigned Issues: {summary['total_assigned']}")
        lines.append(f"  • In Progress: {summary['in_progress_count']}")
        lines.append(f"  • Due This Week: {summary['due_this_week_count']}")
        if summary['sprint_issues_count'] > 0:
            lines.append(f"  • Sprint Issues: {summary['sprint_issues_count']}")
        lines.append("")
        
        # In Progress Issues
        if agenda['in_progress']:
            lines.append("🚀 IN PROGRESS")
            lines.append("-" * 80)
            for issue in agenda['in_progress']:
                lines.append(f"  [{issue['key']}] {issue['summary']}")
                lines.append(f"    Priority: {issue['priority']} | Status: {issue['status']}")
                lines.append(f"    {issue['url']}")
                lines.append("")
        
        # Due This Week
        if agenda['due_this_week']:
            lines.append("⏰ DUE THIS WEEK")
            lines.append("-" * 80)
            for issue in agenda['due_this_week']:
                lines.append(f"  [{issue['key']}] {issue['summary']}")
                lines.append(f"    Due: {issue['duedate']} | Priority: {issue['priority']}")
                lines.append(f"    {issue['url']}")
                lines.append("")
        
        # Sprint Issues
        if agenda['sprint_issues']:
            lines.append("🏃 CURRENT SPRINT")
            lines.append("-" * 80)
            for issue in agenda['sprint_issues'][:10]:  # Limit to 10
                lines.append(f"  [{issue['key']}] {issue['summary']}")
                lines.append(f"    Status: {issue['status']} | Priority: {issue['priority']}")
                lines.append(f"    {issue['url']}")
                lines.append("")
        
        # Top Priority Assigned
        if agenda['assigned_issues']:
            lines.append("📋 TOP PRIORITY ASSIGNED ISSUES")
            lines.append("-" * 80)
            for issue in agenda['assigned_issues'][:5]:  # Top 5
                lines.append(f"  [{issue['key']}] {issue['summary']}")
                lines.append(f"    Priority: {issue['priority']} | Status: {issue['status']}")
                lines.append(f"    {issue['url']}")
                lines.append("")
        
        # Recently Updated
        if agenda['recently_updated']:
            lines.append("🔄 RECENTLY UPDATED (Last 7 Days)")
            lines.append("-" * 80)
            for issue in agenda['recently_updated'][:5]:  # Top 5
                lines.append(f"  [{issue['key']}] {issue['summary']}")
                lines.append(f"    Updated: {issue['updated'][:10]} | Status: {issue['status']}")
                lines.append(f"    {issue['url']}")
                lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"Generated at: {agenda['generated_at']}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def format_agenda_as_markdown(self, agenda: Dict[str, Any]) -> str:
        """
        Format agenda dictionary as Markdown optimized for Agent consumption.
        
        Args:
            agenda: Agenda dictionary from generate_weekly_agenda
            
        Returns:
            Formatted Markdown string with structured metadata and actionable focus areas
        """
        lines = []
        
        # Import helper methods from report generator if available
        def get_priority_badge(priority: str) -> str:
            badges = {'Highest': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢', 'Lowest': '⚪'}
            return badges.get(priority, '⚫')
        
        def get_status_emoji(status: str) -> str:
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
        
        def create_progress_bar(value: int, total: int, width: int = 15) -> str:
            if total == 0:
                return "░" * width
            filled = int((value / total) * width)
            return "█" * filled + "░" * (width - filled)
        
        summary = agenda['summary']
        
        # Header with structured metadata
        lines.append(f"# 📅 Weekly Agenda")
        lines.append("")
        lines.append("## 📋 Report Metadata")
        lines.append("")
        lines.append("```yaml")
        lines.append("report_type: weekly_agenda")
        lines.append(f"week_start: {agenda['week_start']}")
        lines.append(f"week_end: {agenda['week_end']}")
        lines.append(f"generated_at: {agenda['generated_at']}")
        lines.append(f"total_assigned: {summary['total_assigned']}")
        lines.append(f"in_progress: {summary['in_progress_count']}")
        lines.append(f"due_this_week: {summary['due_this_week_count']}")
        lines.append(f"sprint_issues: {summary['sprint_issues_count']}")
        lines.append(f"recently_updated: {summary['recently_updated_count']}")
        lines.append("```")
        lines.append("")
        
        # Actionable Focus Areas
        lines.append("## 🎯 This Week's Focus")
        lines.append("")
        focus_areas = []
        if summary['due_this_week_count'] > 0:
            focus_areas.append(f"- **{summary['due_this_week_count']} items due this week** - Prioritize completion")
        if summary['in_progress_count'] > 0:
            focus_areas.append(f"- **{summary['in_progress_count']} items in progress** - Push to completion")
        
        # Calculate todo count
        completed = summary.get('completed_count', 0)
        todo = summary['total_assigned'] - summary['in_progress_count'] - completed
        if todo > 0:
            focus_areas.append(f"- **{todo} items to start** - Plan your work")
        
        if focus_areas:
            for area in focus_areas:
                lines.append(area)
        else:
            lines.append("- ✅ No critical items this week - Focus on planning ahead")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Summary Dashboard
        lines.append("## 📊 Your Weekly Summary")
        lines.append("")
        lines.append("<table>")
        lines.append("<tr>")
        lines.append(f'<td align="center"><h3>📋<br/>{summary["total_assigned"]}</h3><sub>Total Assigned</sub></td>')
        lines.append(f'<td align="center"><h3>🔄<br/>{summary["in_progress_count"]}</h3><sub>In Progress</sub></td>')
        lines.append(f'<td align="center"><h3>⏰<br/>{summary["due_this_week_count"]}</h3><sub>Due This Week</sub></td>')
        if summary['sprint_issues_count'] > 0:
            lines.append(f'<td align="center"><h3>🏃<br/>{summary["sprint_issues_count"]}</h3><sub>Sprint Issues</sub></td>')
        lines.append("</tr>")
        lines.append("</table>")
        lines.append("")
        
        # Workload Progress
        if summary['total_assigned'] > 0:
            completed = summary.get('completed_count', 0)
            in_progress = summary['in_progress_count']
            todo = summary['total_assigned'] - in_progress - completed
            
            lines.append("**Workload Progress:**")
            lines.append("")
            if completed > 0:
                lines.append(f"- ✅ Completed: `{completed}` {create_progress_bar(completed, summary['total_assigned'])} {(completed/summary['total_assigned']*100):.0f}%")
            lines.append(f"- 🔄 In Progress: `{in_progress}` {create_progress_bar(in_progress, summary['total_assigned'])} {(in_progress/summary['total_assigned']*100):.0f}%")
            lines.append(f"- 📋 To Do: `{todo}` {create_progress_bar(todo, summary['total_assigned'])} {(todo/summary['total_assigned']*100):.0f}%")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # In Progress Issues - HIGHEST PRIORITY
        if agenda['in_progress']:
            lines.append("## 🚀 In Progress (Continue Work)")
            lines.append("")
            lines.append("*These items are already started and should be pushed to completion.*")
            lines.append("")
            lines.append("| Issue | Summary | Priority | Status |")
            lines.append("|-------|---------|----------|--------|")
            for issue in agenda['in_progress']:
                priority_badge = get_priority_badge(issue['priority'])
                status_emoji = get_status_emoji(issue['status'])
                summary_text = issue['summary'][:50] + '...' if len(issue['summary']) > 50 else issue['summary']
                lines.append(f"| [{issue['key']}]({issue['url']}) | {summary_text} | {priority_badge} {issue['priority']} | {status_emoji} {issue['status']} |")
            lines.append("")
        
        # Due This Week - URGENT
        if agenda['due_this_week']:
            lines.append("## ⏰ Due This Week (Urgent)")
            lines.append("")
            lines.append("*These items have approaching deadlines and need immediate attention.*")
            lines.append("")
            lines.append("| Issue | Summary | Due Date | Priority |")
            lines.append("|-------|---------|----------|----------|")
            for issue in agenda['due_this_week']:
                priority_badge = get_priority_badge(issue['priority'])
                summary_text = issue['summary'][:50] + '...' if len(issue['summary']) > 50 else issue['summary']
                lines.append(f"| [{issue['key']}]({issue['url']}) | {summary_text} | 📅 {issue['duedate']} | {priority_badge} {issue['priority']} |")
            lines.append("")
        
        # Sprint Issues
        if agenda['sprint_issues']:
            lines.append("## 🏃 Current Sprint")
            lines.append("")
            lines.append("*All items committed for this sprint.*")
            lines.append("")
            lines.append("<details>")
            lines.append(f"<summary><b>📋 View All Sprint Issues ({len(agenda['sprint_issues'])})</b></summary>")
            lines.append("")
            lines.append("| Issue | Summary | Status | Priority |")
            lines.append("|-------|---------|--------|----------|")
            for issue in agenda['sprint_issues'][:15]:
                priority_badge = get_priority_badge(issue['priority'])
                status_emoji = get_status_emoji(issue['status'])
                summary_text = issue['summary'][:45] + '...' if len(issue['summary']) > 45 else issue['summary']
                lines.append(f"| [{issue['key']}]({issue['url']}) | {summary_text} | {status_emoji} {issue['status']} | {priority_badge} {issue['priority']} |")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # Top Priority Assigned - PLAN AHEAD
        if agenda['assigned_issues']:
            lines.append("## 📋 Top Priority Assigned Issues")
            lines.append("")
            lines.append("*Plan your work by selecting from these assigned items.*")
            lines.append("")
            lines.append("<details>")
            lines.append(f"<summary><b>📋 View Top {min(10, len(agenda['assigned_issues']))} Issues</b></summary>")
            lines.append("")
            lines.append("| Issue | Summary | Priority | Status |")
            lines.append("|-------|---------|----------|--------|")
            for issue in agenda['assigned_issues'][:10]:
                priority_badge = get_priority_badge(issue['priority'])
                status_emoji = get_status_emoji(issue['status'])
                summary_text = issue['summary'][:50] + '...' if len(issue['summary']) > 50 else issue['summary']
                lines.append(f"| [{issue['key']}]({issue['url']}) | {summary_text} | {priority_badge} {issue['priority']} | {status_emoji} {issue['status']} |")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # Recently Updated
        if agenda['recently_updated']:
            lines.append("## 🔄 Recently Updated (Last 7 Days)")
            lines.append("")
            lines.append("*Context: Items that have been recently updated in your workspace.*")
            lines.append("")
            lines.append("<details>")
            lines.append(f"<summary><b>📝 View Recently Updated Issues ({len(agenda['recently_updated'])})</b></summary>")
            lines.append("")
            lines.append("| Issue | Summary | Updated | Status |")
            lines.append("|-------|---------|---------|--------|")
            for issue in agenda['recently_updated'][:10]:
                status_emoji = get_status_emoji(issue['status'])
                summary_text = issue['summary'][:45] + '...' if len(issue['summary']) > 45 else issue['summary']
                lines.append(f"| [{issue['key']}]({issue['url']}) | {summary_text} | 📅 {issue['updated'][:10]} | {status_emoji} {issue['status']} |")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("<div align='center'>")
        lines.append(f"<sub>📅 Weekly Agenda | {agenda['week_start']} - {agenda['week_end']} | 🤖 Generated by Abulafia</sub>")
        lines.append("</div>")
        
        return "\n".join(lines)
    
    def format_agenda_as_marp(self, agenda: Dict[str, Any]) -> str:
        """
        Format agenda as Marp presentation.
        
        Args:
            agenda: Agenda dictionary
            
        Returns:
            Formatted Marp markdown string
        """
        def get_priority_badge(priority: str) -> str:
            badges = {'Highest': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢', 'Lowest': '⚪'}
            return badges.get(priority, '⚫')
        
        def get_status_emoji(status: str) -> str:
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
        
        lines = []
        
        # Marp frontmatter
        lines.append("---")
        lines.append("marp: true")
        lines.append("theme: default")
        lines.append("paginate: true")
        lines.append("header: '📅 Weekly Agenda'")
        lines.append(f"footer: '{agenda['week_start']} - {agenda['week_end']}'")
        lines.append("---")
        lines.append("")
        
        # Title slide
        lines.append("<!-- _class: lead -->")
        lines.append("")
        lines.append("# 📅 Weekly Agenda")
        lines.append("")
        lines.append(f"## {agenda['week_start']} to {agenda['week_end']}")
        lines.append("")
        lines.append("_Your personalized Jira task overview_")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Summary slide
        lines.append("# 📊 Week Overview")
        lines.append("")
        summary = agenda['summary']
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| 📋 **Total Assigned** | {summary['total_assigned']} |")
        lines.append(f"| 🔄 **In Progress** | {summary['in_progress_count']} |")
        lines.append(f"| ⏰ **Due This Week** | {summary['due_this_week_count']} |")
        lines.append(f"| 🎯 **Sprint Items** | {summary['sprint_issues_count']} |")
        lines.append(f"| 🔄 **Recently Updated** | {summary['recently_updated_count']} |")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # In Progress Issues
        if agenda['in_progress']:
            lines.append("# 🔄 In Progress")
            lines.append("")
            for issue in agenda['in_progress'][:5]:
                badge = get_priority_badge(issue['priority'])
                lines.append(f"### {badge} [{issue['key']}]({issue['url']})")
                lines.append(f"**{issue['summary']}**")
                lines.append("")
                if issue.get('description') and isinstance(issue['description'], str) and issue['description']:
                    desc = issue['description'][:150] + '...' if len(issue['description']) > 150 else issue['description']
                    lines.append(f"_{desc}_")
                    lines.append("")
            lines.append("---")
            lines.append("")
        
        # Due This Week
        if agenda['due_this_week']:
            lines.append("# ⏰ Due This Week")
            lines.append("")
            for issue in agenda['due_this_week'][:6]:
                badge = get_priority_badge(issue['priority'])
                emoji = get_status_emoji(issue['status'])
                lines.append(f"- {badge} **[{issue['key']}]({issue['url']})** - {issue['summary'][:60]}")
                lines.append(f"  - Status: {emoji} {issue['status']}")
                if issue['duedate']:
                    lines.append(f"  - Due: 📅 {issue['duedate']}")
                lines.append("")
            lines.append("---")
            lines.append("")
        
        # Sprint Issues
        if agenda['sprint_issues']:
            lines.append("# 🎯 Current Sprint")
            lines.append("")
            for issue in agenda['sprint_issues'][:6]:
                badge = get_priority_badge(issue['priority'])
                emoji = get_status_emoji(issue['status'])
                lines.append(f"- {badge} **[{issue['key']}]({issue['url']})** - {issue['summary'][:60]}")
                lines.append(f"  - {emoji} {issue['status']}")
                lines.append("")
            lines.append("---")
            lines.append("")
        
        # Top Priority
        if agenda['assigned_issues']:
            lines.append("# 🎯 Top Priorities")
            lines.append("")
            for issue in agenda['assigned_issues'][:5]:
                badge = get_priority_badge(issue['priority'])
                emoji = get_status_emoji(issue['status'])
                lines.append(f"### {badge} {issue['priority']}: [{issue['key']}]({issue['url']})")
                lines.append(f"**{issue['summary']}**")
                lines.append(f"{emoji} _{issue['status']}_")
                lines.append("")
            lines.append("---")
            lines.append("")
        
        # Final slide
        lines.append("<!-- _class: lead -->")
        lines.append("")
        lines.append("# 🎯 Focus & Execute")
        lines.append("")
        lines.append(f"## {summary['in_progress_count']} tasks in progress")
        lines.append(f"## {summary['due_this_week_count']} items due this week")
        lines.append("")
        lines.append("_Generated by Abulafia Bot 🤖_")
        
        return "\n".join(lines)
