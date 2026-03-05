# Abulafia - Jira Reports & Analytics for Agent Consumption

A Python tool that connects to Jira via API and generates comprehensive reports optimized for AI Agent consumption. Perfect for use with MCP Atlassian and other AI assistants to analyze project status, team performance, and workflow bottlenecks.

## Features

- 🔗 **Jira API Integration** - Connects to your Jira instance via REST API
- 📅 **Automatic Weekly Agenda Generation** - Pulls and organizes your Jira issues for the week
- 👥 **Team Activity Tracking** - Monitor all team members' tasks and progress
- ⚠️ **Bottleneck Detection** - Automatically identifies stale issues, aging work, and workflow risks
- 📈 **Historical Reports** - Generate reports for last week/month activities
- 🎨 **Enhanced Markdown Reports** - Structured reports with tables, progress bars, badges, and metadata
- 🤖 **Agent-Optimized Output** - Reports include structured metadata, actionable insights, and context
- 🧠 **Actionable Recommendations** - Auto-generated suggestions based on workflow analysis
- 📊 **Smart Issue Categorization** - Organizes issues by status, priority, due dates, and sprints
- 📝 **Export Capabilities** - Save all reports as Text, Markdown, or Marp Presentations
- 🎯 **Multiple Views** - View assigned issues, in-progress tasks, sprint items, and more
- 🗂️ **Multi-Project Support** - Aggregate reports across multiple Jira projects

## What the Reports Include

### Personal Weekly Agenda
- **Structured Metadata** - YAML-formatted report metadata for easy Agent parsing
- **Actionable Focus Areas** - Key priorities and recommended actions for the week
- **Summary Statistics** - Overview of your workload
- **In Progress Issues** - Tasks you're currently working on (prioritized for completion)
- **Due This Week** - Upcoming deadlines (urgent items)
- **Current Sprint** - Sprint backlog items
- **Top Priority Issues** - Highest priority assigned tasks
- **Recently Updated** - Issues with recent activity for context

### Team Activity Report
- **Structured Metadata** - YAML-formatted report metadata with key metrics
- **Key Insights & Recommended Actions** - Auto-generated actionable recommendations
- **Team Overview** - All team members and their task counts
- **Status Breakdown** - Issues organized by status across the team
- **Per-Member Details** - Individual stats and top issues for each team member
- **Priority Analysis** - Priority distribution across team members
- **⚠️ Bottleneck Detection** - Identifies workflow issues and risks:
  - **Stale Issues** - Tasks not updated in 7+ days (potential blockers)
  - **Aging Work** - Issues in progress for 14+ days
  - **High Priority At Risk** - Critical items taking too long
  - **Workload Imbalance** - Team members with 50%+ above average workload
  - **Blocked Status** - Issues explicitly marked as blocked

### Historical Reports
- **Completed Issues** - All issues finished in the period
- **Team Productivity** - How many issues each member completed, updated, or created
- **Activity Timeline** - When issues were created, updated, and completed
- **Period Comparison** - Statistics for last week, last month, current week, or current month

## 🤖 Agent-Optimized Reports

All markdown reports include structured elements optimized for AI Agent consumption:

- **📋 YAML Metadata Blocks** - Structured report metadata for easy parsing
- **🎯 Actionable Insights** - Auto-generated recommendations based on data analysis
- **📊 Clear Context** - Descriptive section headers explaining what each section means
- **📈 Progress Visualization** - Progress bars and percentage breakdowns
- **🎨 Priority Indicators** - Color-coded emojis (🔴 Highest, 🟠 High, 🟡 Medium, 🟢 Low)
- **✨ Status Badges** - Emoji indicators (✅ Done, 🔄 In Progress, 👀 Review, 🚫 Blocked)
- **📦 Organized Sections** - Collapsible details for scalable information
- **🏷️ Categorized Data** - Issues organized by priority, status, and urgency

Perfect for AI Agents using MCP Atlassian or similar tools to analyze project health!

## 📊 Marp Presentation Export

Export any report as a **Marp presentation** for slide-based viewing:

- **🎭 Slide Format** - Professional presentation layout
- **📽️ Export to PDF/PPTX** - Convert to PowerPoint or PDF
- **🎨 Themed Slides** - Beautiful default theme with pagination
- **📈 Visual Data** - Charts, metrics, and team performance in slides

**How to use:**
1. Select Option 9 (Export Reports) from main menu
2. Choose your report type
3. Select format "3. Marp Presentation (.md)"
4. Open with Marp CLI or VS Code Marp extension
5. Export to PDF/PPTX for presentations

**Tools:**
- **VS Code**: Install "Marp for VS Code" extension
- **CLI**: `npm install -g @marp-team/marp-cli`
- **Convert**: `marp yourfile_presentation.md --pdf`

## Prerequisites

- Python 3.8 or higher
- Jira account with API access
## Installation

### 1. Clone or Download the Project

```bash
cd abulafia
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   copy .env.example .env  # On Windows
   # cp .env.example .env  # On Linux/Mac
   ```

2. Edit `.env` and fill in your credentials:

```env
# Jira Configuration
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token

# Optional: Jira Project Configuration
JIRA_PROJECT_KEY=PROJ
JIRA_BOARD_ID=123
```

### 5. Configure Multiple Projects (Optional)

For multi-project aggregate reporting, create a `config.json` file:

```bash
copy config.json.example config.json  # On Windows
# cp config.json.example config.json  # On Linux/Mac
```

Edit `config.json` to add your Jira projects:

```json
{
  "projects": [
    {
      "name": "Main Project",
      "key": "MAR",
      "board_id": "1",
      "enabled": true,
      "description": "Primary development project"
    },
    {
      "name": "Infrastructure",
      "key": "INFRA",
      "board_id": "2",
      "enabled": true,
      "description": "Infrastructure and DevOps tasks"
    }
  ],
  "settings": {
    "aggregate_reports": true,
    "default_max_results": 200,
    "stale_threshold_days": 7,
    "aging_threshold_days": 14
  }
}
```

**Benefits of Multi-Project Configuration:**
- 📊 **Aggregate Reports** - Combine data from multiple Jira spaces
- 🔍 **Cross-Project Visibility** - See all your team's work in one view
- 📈 **Unified Analytics** - Bottleneck detection across all projects
- 🎯 **Flexible Selection** - Choose single project or aggregate on-demand

**Note:** If you don't create a `config.json`, the system will use the legacy single-project mode from `.env`

## Getting Jira API Token

1. Go to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "Abulafia Reports")
4. Copy the token and paste it in your `.env` file

## Usage with AI Agents

Abulafia generates structured Markdown reports optimized for consumption by AI Agents (like those using MCP Atlassian). The reports include:

- **Structured YAML metadata** - Easy parsing for agents
- **Actionable insights** - Auto-generated recommendations
- **Clear context** - Descriptive explanations of what each section means
- **Organized data** - Issues categorized by priority, status, and urgency

Simply generate reports and have your AI Agent read and analyze them for project insights, bottleneck identification, and action planning.

## Usage

### Running the Application

```bash
python main.py
```

### Main Menu Options

1. **Generate Weekly Agenda (Personal)** - Creates your personal comprehensive agenda from Jira
2. **View My Assigned Issues** - Quick list of your assigned tasks
3. **View In Progress Issues** - See what you're currently working on
4. **Test Jira Connection** - Verify your Jira credentials
5. **Generate Team Report** - Comprehensive team activity report with multi-project support
6. **Generate Historical Report** - Historical activity reports with multi-project aggregation
7. **Export Reports** - Save any report to file (Text, Markdown, or Marp Presentation)
8. **Exit** - Close the application

When you have multiple projects configured in `config.json`, options 5 and 6 will prompt you to:
- Select a single project report, OR
- Generate an aggregate report across all projects

### Example Report Outputs

#### Team Report
```
👥 TEAM ACTIVITY REPORT
================================================================================

📊 TEAM SUMMARY
--------------------------------------------------------------------------------
  • Team Members: 5
  • Total Active Issues: 23
  
  Status Breakdown:
    - In Progress: 8
    - To Do: 10
    - In Review: 5

👤 TEAM MEMBER DETAILS
--------------------------------------------------------------------------------

Alice Smith
  Total Issues: 6
  By Status:
    - In Progress: 3
    - In Review: 2
    - To Do: 1
  Top Issues:
    - [PROJ-123] Implement new feature (In Progress)
    - [PROJ-124] Fix critical bug (In Progress)
```

#### Historical Report
```
📈 HISTORICAL ACTIVITY REPORT - LAST WEEK
Period: 2026-02-24 to 2026-03-02
================================================================================

📊 ACTIVITY SUMMARY
--------------------------------------------------------------------------------
  • Issues Completed: 12
  • Issues Updated: 28
  • Issues Created: 8
  • Active Team Members: 5

👥 TEAM PRODUCTIVITY
--------------------------------------------------------------------------------

Alice Smith
  ✅ Completed: 4
  🔄 Updated: 8
  ➕ Created: 2
  Completed Issues:
    - [PROJ-123] Implement authentication
    - [PROJ-125] Update documentation
```

## Project Structure

```
abulafia/
├── main.py                 # Main application entry point
├── config.py               # Configuration management
├── jira_client.py          # Jira API integration
├── agenda_generator.py     # Weekly agenda generation logic
├── report_generator.py     # Team and historical report generation
├── chatbot.py              # AI chatbot interface
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your actual credentials (not in git)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Customization

### Modifying Reports

Edit `agenda_generator.py` to customize personal agendas:
- What issues are included
- How issues are categorized
- The format and structure of the output
- Metadata fields included

Edit `report_generator.py` to customize team and historical reports:
- Date range calculations
- Team member filtering
- Report formatting and sections
- Actionable insight generation
- Bottleneck detection thresholds

### Adding New Jira Queries

Add new methods to `jira_client.py` to fetch:
- Custom filters
- Specific project data
- Team-wide information

## 🧪 Testing

A comprehensive test suite is available to validate all CLI functionalities.

### Quick Start

**Windows:**
```bash
run_tests.bat
```

**Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

**Manual Execution:**
```bash
python test_suite.py
```

### What's Tested

The test suite validates:

1. ✅ **Jira Connection** - API connectivity and authentication
2. ✅ **Agenda Generation** - Markdown and Marp formats with YAML metadata
3. ✅ **Team Reports** - Markdown and text formats with actionable insights
4. ✅ **Historical Reports** - Period-based activity analysis
5. ✅ **CLI Commands** - All command-line interface tools
6. ✅ **Output Validation** - YAML metadata, required sections, file creation
7. ✅ **Format Variations** - Text, markdown, and Marp presentation formats

### Running with pytest (Optional)

For enhanced test reporting:

```bash
pip install pytest
pytest test_suite.py -v
```

### Test Results

All test outputs are saved to `output/test_results/` for manual inspection.

See [TEST_GUIDE.md](TEST_GUIDE.md) for detailed information about:
- Individual test descriptions
- Troubleshooting test failures
- Extending the test suite
- CI/CD integration

## Troubleshooting

### "Configuration Error" on startup
- Make sure `.env` file exists
- Verify all required variables are set
- Check that credentials are correct

### "Jira connection failed"
- Verify JIRA_SERVER URL (should include https://)
- Check JIRA_EMAIL matches your Atlassian account
- Regenerate API token if needed
- Ensure you have permission to access the Jira instance

### "No issues found"
- Check that you have issues assigned to you
- Verify JIRA_PROJECT_KEY if specified
- Try generating agenda from the main menu first

## Security Notes

- Never commit your `.env` file to version control
- Keep your API tokens secure
- Rotate tokens periodically
- Use read-only Jira permissions if possible

## Contributing

Feel free to extend this project with:
- Additional Jira queries and filters
- More report formats
- Web interface
- Slack/Teams integration
- Calendar integration
- Notification system

## License

This project is provided as-is for personal and commercial use.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review Jira API documentation: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

---

**Happy Project Managing! 🚀**
