"""Main application for Abulafia - Jira Reports & Analytics."""
import sys
import os
import argparse
from src.config import Config
from src.clients.jira_client import JiraClient
from src.generators.agenda_generator import AgendaGenerator
from src.generators.report_generator import ReportGenerator

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


def print_banner():
    """Print application banner."""
    print("\n" + "=" * 80)
    print("  Abulafia - Jira Reports & Analytics for Agent Consumption")
    print("=" * 80 + "\n")


def print_menu():
    """Print main menu options."""
    print("\nAvailable Commands:")
    print("  1. Generate Weekly Agenda (Personal)")
    print("  2. View My Assigned Issues")
    print("  3. View In Progress Issues")
    print("  4. Test Jira Connection")
    print("  5. Generate Team Report (Multi-Project Support)")
    print("  6. Generate Historical Report (Multi-Project Support)")
    print("  7. Export Reports (Text/Markdown/Marp)")
    print("  8. Exit")
    print("-" * 80)


def generate_agenda(agenda_gen: AgendaGenerator):
    """Generate and display weekly agenda."""
    print("\n📅 Generating Weekly Agenda...")
    try:
        agenda = agenda_gen.generate_weekly_agenda()
        text_output = agenda_gen.format_agenda_as_text(agenda)
        print("\n" + text_output)
    except Exception as e:
        print(f"❌ Error generating agenda: {e}")


def export_agenda(agenda_gen: AgendaGenerator):
    """Export agenda to file."""
    print("\nExport Format:")
    print("  1. Text (.txt)")
    print("  2. Markdown (.md)")
    choice = input("\nSelect format (1-2): ").strip()
    
    try:
        agenda = agenda_gen.generate_weekly_agenda()
        
        # Ensure output directory exists
        output_dir = os.path.join(os.path.dirname(__file__), 'output', 'agendas')
        os.makedirs(output_dir, exist_ok=True)
        
        if choice == '1':
            content = agenda_gen.format_agenda_as_text(agenda)
            filename = os.path.join(output_dir, f"agenda_{agenda['week_start']}.txt")
        elif choice == '2':
            content = agenda_gen.format_agenda_as_markdown(agenda)
            filename = os.path.join(output_dir, f"agenda_{agenda['week_start']}.md")
        else:
            print("Invalid choice.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ Agenda exported to: {filename}")
    except Exception as e:
        print(f"❌ Error exporting agenda: {e}")


def view_assigned_issues(jira_client: JiraClient):
    """View assigned issues."""
    print("\n📋 Your Assigned Issues...")
    try:
        issues = jira_client.get_assigned_issues(max_results=10)
        if not issues:
            print("No assigned issues found.")
            return
        
        print(f"\nFound {len(issues)} assigned issues:\n")
        for issue in issues:
            issue_data = jira_client.format_issue(issue)
            print(f"  [{issue_data['key']}] {issue_data['summary']}")
            print(f"    Status: {issue_data['status']} | Priority: {issue_data['priority']}")
            print(f"    {issue_data['url']}\n")
    except Exception as e:
        print(f"❌ Error: {e}")


def view_in_progress(jira_client: JiraClient):
    """View in-progress issues."""
    print("\n🚀 Issues In Progress...")
    try:
        issues = jira_client.get_issues_by_status("In Progress")
        if not issues:
            print("No issues in progress.")
            return
        
        print(f"\nFound {len(issues)} issues in progress:\n")
        for issue in issues:
            issue_data = jira_client.format_issue(issue)
            print(f"  [{issue_data['key']}] {issue_data['summary']}")
            print(f"    Priority: {issue_data['priority']}")
            print(f"    {issue_data['url']}\n")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_connection(jira_client: JiraClient):
    """Test Jira connection."""
    print("\n🔌 Testing Jira Connection...")
    try:
        if jira_client.test_connection():
            user = jira_client.get_current_user()
            print(f"✅ Connected successfully!")
            print(f"   Logged in as: {user['displayName']} ({user['emailAddress']})")
        else:
            print("❌ Connection failed.")
    except Exception as e:
        print(f"❌ Connection error: {e}")


def generate_team_report(report_gen: ReportGenerator):
    """Generate and display team report."""
    # Load projects from config
    Config.load_config_file()
    projects = Config.get_projects()
    
    # If multiple projects available, ask user
    if len(projects) > 1:
        print("\n📦 Available Projects:")
        for i, proj in enumerate(projects, 1):
            print(f"  {i}. {proj['name']} ({proj['key']})")
        print(f"  {len(projects) + 1}. Aggregate Report (All Projects)")
        
        choice = input(f"\nSelect project or aggregate (1-{len(projects) + 1}): ").strip()
        
        try:
            choice_idx = int(choice) - 1
            if choice_idx == len(projects):
                # Aggregate mode
                project_keys = [p['key'] for p in projects]
                print(f"\n👥 Generating Aggregate Team Report across {len(project_keys)} projects...")
            elif 0 <= choice_idx < len(projects):
                # Single project
                project_keys = [projects[choice_idx]['key']]
                print(f"\n👥 Generating Team Report for {projects[choice_idx]['name']}...")
            else:
                print("Invalid choice.")
                return None
        except (ValueError, IndexError):
            print("Invalid choice.")
            return None
    else:
        # Single project mode
        project_keys = [projects[0]['key']] if projects else None
        print("\n👥 Generating Team Report...")
    
    try:
        report = report_gen.generate_team_report(project_keys=project_keys)
        text_output = report_gen.format_team_report_as_text(report)
        print("\n" + text_output)
        return report
    except Exception as e:
        print(f"❌ Error generating team report: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_historical_report(report_gen: ReportGenerator):
    """Generate and display historical report."""
    # Load projects from config
    Config.load_config_file()
    projects = Config.get_projects()
    
    # Project selection
    project_keys = None
    if len(projects) > 1:
        print("\n📦 Available Projects:")
        for i, proj in enumerate(projects, 1):
            print(f"  {i}. {proj['name']} ({proj['key']})")
        print(f"  {len(projects) + 1}. Aggregate Report (All Projects)")
        
        choice = input(f"\nSelect project or aggregate (1-{len(projects) + 1}): ").strip()
        
        try:
            choice_idx = int(choice) - 1
            if choice_idx == len(projects):
                project_keys = [p['key'] for p in projects]
            elif 0 <= choice_idx < len(projects):
                project_keys = [projects[choice_idx]['key']]
            else:
                print("Invalid choice.")
                return None
        except (ValueError, IndexError):
            print("Invalid choice.")
            return None
    else:
        project_keys = [projects[0]['key']] if projects else None
    
    # Period selection
    print("\nSelect Period:")
    print("  1. Last Week")
    print("  2. Last Month")
    print("  3. Current Week")
    print("  4. Current Month")
    choice = input("\nSelect period (1-4): ").strip()
    
    period_map = {
        '1': 'last_week',
        '2': 'last_month',
        '3': 'current_week',
        '4': 'current_month'
    }
    
    if choice not in period_map:
        print("Invalid choice.")
        return None
    
    period = period_map[choice]
    
    if project_keys and len(project_keys) > 1:
        print(f"\n📈 Generating Aggregate Historical Report for {period.replace('_', ' ').title()}...")
    else:
        print(f"\n📈 Generating Historical Report for {period.replace('_', ' ').title()}...")
    
    try:
        report = report_gen.generate_historical_report(period, project_keys=project_keys)
        text_output = report_gen.format_historical_report_as_text(report)
        print("\n" + text_output)
        return report
    except Exception as e:
        print(f"❌ Error generating historical report: {e}")
        import traceback
        traceback.print_exc()
        return None


def export_reports(agenda_gen: AgendaGenerator, report_gen: ReportGenerator):
    """Export reports to file."""
    print("\nSelect Report Type:")
    print("  1. Personal Weekly Agenda")
    print("  2. Team Report")
    print("  3. Historical Report (Last Week)")
    print("  4. Historical Report (Last Month)")
    report_choice = input("\nSelect report type (1-4): ").strip()
    
    print("\nExport Format:")
    print("  1. Text (.txt)")
    print("  2. Markdown (.md)")
    print("  3. Marp Presentation (.md)")
    format_choice = input("\nSelect format (1-3): ").strip()
    
    try:
        if report_choice == '1':
            report = agenda_gen.generate_weekly_agenda()
            if format_choice == '1':
                content = agenda_gen.format_agenda_as_text(report)
                filename = f"agenda_{report['week_start']}.txt"
            elif format_choice == '2':
                content = agenda_gen.format_agenda_as_markdown(report)
                filename = f"agenda_{report['week_start']}.md"
            elif format_choice == '3':
                content = agenda_gen.format_agenda_as_marp(report)
                filename = f"agenda_{report['week_start']}_presentation.md"
            else:
                print("Invalid format choice.")
                return
        
        elif report_choice == '2':
            # Load config for potential multi-project selection
            Config.load_config_file()
            projects = Config.get_projects()
            
            project_keys = None
            if len(projects) > 1:
                print("\n📦 Projects:")
                for i, proj in enumerate(projects, 1):
                    print(f"  {i}. {proj['name']} ({proj['key']})")
                print(f"  {len(projects) + 1}. Aggregate (All)")
                
                proj_choice = input(f"\nSelect (1-{len(projects) + 1}): ").strip()
                try:
                    idx = int(proj_choice) - 1
                    if idx == len(projects):
                        project_keys = [p['key'] for p in projects]
                    elif 0 <= idx < len(projects):
                        project_keys = [projects[idx]['key']]
                except (ValueError, IndexError):
                    pass
            
            report = report_gen.generate_team_report(project_keys=project_keys)
            if format_choice == '1':
                content = report_gen.format_team_report_as_text(report)
                filename = f"team_report_{report['generated_at'][:10]}.txt"
            elif format_choice == '2':
                content = report_gen.format_team_report_as_markdown(report)
                filename = f"team_report_{report['generated_at'][:10]}.md"
            elif format_choice == '3':
                content = report_gen.format_team_report_as_marp(report)
                filename = f"team_report_{report['generated_at'][:10]}_presentation.md"
            else:
                print("Invalid format choice.")
                return
        
        elif report_choice in ['3', '4']:
            # Load config for potential multi-project selection
            Config.load_config_file()
            projects = Config.get_projects()
            
            project_keys = None
            if len(projects) > 1:
                print("\n📦 Projects:")
                for i, proj in enumerate(projects, 1):
                    print(f"  {i}. {proj['name']} ({proj['key']})")
                print(f"  {len(projects) + 1}. Aggregate (All)")
                
                proj_choice = input(f"\nSelect (1-{len(projects) + 1}): ").strip()
                try:
                    idx = int(proj_choice) - 1
                    if idx == len(projects):
                        project_keys = [p['key'] for p in projects]
                    elif 0 <= idx < len(projects):
                        project_keys = [projects[idx]['key']]
                except (ValueError, IndexError):
                    pass
            
            period = 'last_week' if report_choice == '3' else 'last_month'
            report = report_gen.generate_historical_report(period, project_keys=project_keys)
            if format_choice == '1':
                content = report_gen.format_historical_report_as_text(report)
                filename = f"historical_{period}_{report['start_date']}.txt"
            elif format_choice == '2':
                content = report_gen.format_historical_report_as_markdown(report)
                filename = f"historical_{period}_{report['start_date']}.md"
            elif format_choice == '3':
                content = report_gen.format_historical_report_as_marp(report)
                filename = f"historical_{period}_{report['start_date']}_presentation.md"
            else:
                print("Invalid format choice.")
                return
        
        else:
            print("Invalid report choice.")
            return
        
        # Ensure output directory exists
        output_dir = os.path.join(os.path.dirname(__file__), 'output', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, filename)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ Report exported to: {filename}")
        
        if format_choice == '3':
            print("\n💡 Tip: Open the .md file with Marp CLI or VS Code Marp extension")
            print("   - VS Code: Install 'Marp for VS Code' extension")
            print("   - CLI: npm install -g @marp-team/marp-cli")
            print("   - Then: marp " + filename + " --pdf")
        
    except Exception as e:
        print(f"❌ Error exporting report: {e}")
        import traceback
        traceback.print_exc()


def parse_arguments():
    """Parse command-line arguments for CLI access to all functionality."""
    parser = argparse.ArgumentParser(
        description="Abulafia - Jira-Powered Project Management Assistant",
        epilog="Run without arguments for interactive mode."
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Agenda command
    agenda_parser = subparsers.add_parser('agenda', help='Generate weekly agenda')
    agenda_parser.add_argument('--format', choices=['text', 'md', 'marp'], default='text',
                               help='Output format (default: text)')
    agenda_parser.add_argument('--output', '-o', help='Output filename')
    
    # Team report command
    team_parser = subparsers.add_parser('team-report', help='Generate team report')
    team_parser.add_argument('--project', '-p', help='Project key (e.g., MAR)')
    team_parser.add_argument('--aggregate', '-a', action='store_true',
                            help='Generate aggregate report for all projects')
    team_parser.add_argument('--format', choices=['text', 'md', 'marp'], default='text',
                            help='Output format (default: text)')
    team_parser.add_argument('--output', '-o', help='Output filename')
    
    # Historical report command
    hist_parser = subparsers.add_parser('historical-report', help='Generate historical report')
    hist_parser.add_argument('--period', choices=['last_week', 'last_month', 'current_week', 'current_month'],
                            default='last_week', help='Time period (default: last_week)')
    hist_parser.add_argument('--project', '-p', help='Project key (e.g., MAR)')
    hist_parser.add_argument('--aggregate', '-a', action='store_true',
                            help='Generate aggregate report for all projects')
    hist_parser.add_argument('--format', choices=['text', 'md', 'marp'], default='text',
                            help='Output format (default: text)')
    hist_parser.add_argument('--output', '-o', help='Output filename')
    
    # Connection test command
    subparsers.add_parser('test-connection', help='Test Jira connection')
    
    # Assigned issues command
    assigned_parser = subparsers.add_parser('assigned-issues', help='View assigned issues')
    assigned_parser.add_argument('--max', type=int, default=10, help='Maximum number of issues (default: 10)')
    
    # In progress issues command
    progress_parser = subparsers.add_parser('in-progress', help='View in-progress issues')
    progress_parser.add_argument('--max', type=int, default=10, help='Maximum number of issues (default: 10)')
    
    return parser.parse_args()


def cli_generate_agenda(agenda_gen: AgendaGenerator, args):
    """CLI: Generate agenda without user interaction."""
    try:
        agenda = agenda_gen.generate_weekly_agenda()
        
        # Format content
        if args.format == 'text':
            content = agenda_gen.format_agenda_as_text(agenda)
            default_ext = 'txt'
        elif args.format == 'md':
            content = agenda_gen.format_agenda_as_markdown(agenda)
            default_ext = 'md'
        else:  # marp
            content = agenda_gen.format_agenda_as_marp(agenda)
            default_ext = 'md'
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            output_dir = os.path.join(os.path.dirname(__file__), 'output', 'agendas')
            os.makedirs(output_dir, exist_ok=True)
            suffix = '_presentation' if args.format == 'marp' else ''
            output_file = os.path.join(output_dir, f"agenda_{agenda['week_start']}{suffix}.{default_ext}")
        
        # Save file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Agenda generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error generating agenda: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cli_generate_team_report(report_gen: ReportGenerator, args):
    """CLI: Generate team report without user interaction."""
    try:
        # Determine project keys
        if args.aggregate:
            Config.load_config_file()
            projects = Config.get_projects()
            project_keys = [p['key'] for p in projects]
        elif args.project:
            project_keys = [args.project]
        else:
            project_keys = None
        
        # Generate report
        report = report_gen.generate_team_report(project_keys=project_keys)
        
        # Format content
        if args.format == 'text':
            content = report_gen.format_team_report_as_text(report)
            default_ext = 'txt'
        elif args.format == 'md':
            content = report_gen.format_team_report_as_markdown(report)
            default_ext = 'md'
        else:  # marp
            content = report_gen.format_team_report_as_marp(report)
            default_ext = 'md'
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            output_dir = os.path.join(os.path.dirname(__file__), 'output', 'reports')
            os.makedirs(output_dir, exist_ok=True)
            suffix = '_presentation' if args.format == 'marp' else ''
            output_file = os.path.join(output_dir, f"team_report_{report['generated_at'][:10]}{suffix}.{default_ext}")
        
        # Save file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Team report generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error generating team report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cli_generate_historical_report(report_gen: ReportGenerator, args):
    """CLI: Generate historical report without user interaction."""
    try:
        # Determine project keys
        if args.aggregate:
            Config.load_config_file()
            projects = Config.get_projects()
            project_keys = [p['key'] for p in projects]
        elif args.project:
            project_keys = [args.project]
        else:
            project_keys = None
        
        # Generate report
        report = report_gen.generate_historical_report(args.period, project_keys=project_keys)
        
        # Format content
        if args.format == 'text':
            content = report_gen.format_historical_report_as_text(report)
            default_ext = 'txt'
        elif args.format == 'md':
            content = report_gen.format_historical_report_as_markdown(report)
            default_ext = 'md'
        else:  # marp
            content = report_gen.format_historical_report_as_marp(report)
            default_ext = 'md'
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            output_dir = os.path.join(os.path.dirname(__file__), 'output', 'reports')
            os.makedirs(output_dir, exist_ok=True)
            suffix = '_presentation' if args.format == 'marp' else ''
            output_file = os.path.join(output_dir, 
                                      f"historical_{args.period}_{report['start_date']}{suffix}.{default_ext}")
        
        # Save file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Historical report generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error generating historical report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cli_test_connection(jira_client: JiraClient):
    """CLI: Test Jira connection."""
    try:
        if jira_client.test_connection():
            user = jira_client.get_current_user()
            print(f"✅ Connected successfully!")
            print(f"   Logged in as: {user['displayName']} ({user['emailAddress']})")
            return True
        else:
            print("❌ Connection failed.")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)


def cli_view_assigned_issues(jira_client: JiraClient, max_results: int = 10):
    """CLI: View assigned issues."""
    try:
        issues = jira_client.get_assigned_issues(max_results=max_results)
        if not issues:
            print("No assigned issues found.")
            return []
        
        print(f"Found {len(issues)} assigned issues:\n")
        for issue in issues:
            issue_data = jira_client.format_issue(issue)
            print(f"[{issue_data['key']}] {issue_data['summary']}")
            print(f"  Status: {issue_data['status']} | Priority: {issue_data['priority']}")
            print(f"  {issue_data['url']}\n")
        return issues
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cli_view_in_progress(jira_client: JiraClient, max_results: int = 10):
    """CLI: View in-progress issues."""
    try:
        issues = jira_client.get_issues_by_status("In Progress", max_results=max_results)
        if not issues:
            print("No issues in progress.")
            return []
        
        print(f"Found {len(issues)} issues in progress:\n")
        for issue in issues:
            issue_data = jira_client.format_issue(issue)
            print(f"[{issue_data['key']}] {issue_data['summary']}")
            print(f"  Priority: {issue_data['priority']}")
            print(f"  {issue_data['url']}\n")
        return issues
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main application entry point."""
    # Parse CLI arguments
    args = parse_arguments()
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration Error:\n{e}\n")
        print("Please create a .env file based on .env.example and fill in your credentials.")
        sys.exit(1)
    
    # Initialize components
    try:
        jira_client = JiraClient()
        agenda_gen = AgendaGenerator(jira_client)
        report_gen = ReportGenerator(jira_client)
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Handle CLI commands
    if args.command:
        if args.command == 'agenda':
            cli_generate_agenda(agenda_gen, args)
        elif args.command == 'team-report':
            cli_generate_team_report(report_gen, args)
        elif args.command == 'historical-report':
            cli_generate_historical_report(report_gen, args)
        elif args.command == 'test-connection':
            cli_test_connection(jira_client)
        elif args.command == 'assigned-issues':
            cli_view_assigned_issues(jira_client, args.max)
        elif args.command == 'in-progress':
            cli_view_in_progress(jira_client, args.max)
        sys.exit(0)
    
    # Interactive mode (original functionality)
    print_banner()
    print("✅ Configuration validated successfully\n")
    
    # Load multi-project configuration
    Config.load_config_file()
    projects = Config.get_projects()
    if projects:
        print(f"📦 Loaded {len(projects)} project(s) from config.json")
        for proj in projects:
            print(f"   - {proj['name']} ({proj['key']})")
        print()
    
    print("Initializing components...")
    print("✅ Initialization complete\n")
    
    # Main loop
    while True:
        print_menu()
        choice = input("\nSelect an option (1-8): ").strip()
        
        if choice == '1':
            generate_agenda(agenda_gen)
        
        elif choice == '2':
            view_assigned_issues(jira_client)
        
        elif choice == '3':
            view_in_progress(jira_client)
        
        elif choice == '4':
            test_connection(jira_client)
        
        elif choice == '5':
            generate_team_report(report_gen)
        
        elif choice == '6':
            generate_historical_report(report_gen)
        
        elif choice == '7':
            export_reports(agenda_gen, report_gen)
        
        elif choice == '8':
            print("\n👋 Goodbye!\n")
            break
        
        else:
            print("\n❌ Invalid choice. Please select 1-8.")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
