# Abulafia - Project Structure

## Directory Structure

```
abulafia/
├── src/                           # Source code
│   ├── clients/                   # API clients
│   │   ├── jira_client.py        # Jira API client
│   │   └── confluence_client.py  # Confluence API client
│   ├── generators/                # Report generators
│   │   ├── report_generator.py   # Team and historical reports
│   │   └── agenda_generator.py   # Weekly agenda generator
│   └── config.py                  # Configuration management
│
├── output/                        # Generated output files
│   ├── reports/                   # Team and historical reports
│   ├── agendas/                   # Weekly agendas
│   └── confluence/                # Downloaded Confluence pages
│
├── main.py                        # Main application entry point
├── confluence_reader.py           # Confluence CLI wrapper
├── config.json                    # Project configuration
├── .env                          # Environment variables
└── requirements.txt              # Python dependencies
```

## Usage

### Main Application
```bash
python main.py
```
Interactive menu for:
- Generating weekly agendas (optimized for Agent consumption)
- Viewing assigned issues
- Viewing in-progress tasks
- Generating team reports with bottleneck detection
- Generating historical activity reports
- Exporting reports in various formats (Text, Markdown, Marp)

### Confluence Reader
```bash
python confluence_reader.py "Page Title"
python confluence_reader.py "Page Title" --output custom_name.html
```
Downloads and saves Confluence pages to `output/confluence/`

### Output Folders

All generated files are saved in their respective output folders:
- **Reports**: `output/reports/` - Team and historical reports (txt, md, marp)
- **Agendas**: `output/agendas/` - Weekly agenda files (txt, md)
- **Confluence**: `output/confluence/` - Downloaded Confluence pages (html)

## AI Agent Optimization

Reports are optimized for AI Agent consumption with:
- **Structured YAML metadata** at the start of each report
- **Actionable insights** auto-generated from data analysis
- **Clear context** with descriptive section headers
- **Categorized data** organized by priority, status, and urgency
- **Progress visualization** with bars and percentages
- **Bottleneck detection** with severity indicators

### Confluence Reader
```bash
python confluence_reader.py "Page Title"
python confluence_reader.py "Page Title" --output custom_name.html
```
Downloads and saves Confluence pages to `output/confluence/`

### Output Folders

All generated files are saved in their respective output folders:
- **Reports**: `output/reports/` - Team and historical reports (txt, md, marp)
- **Agendas**: `output/agendas/` - Weekly agenda files (txt, md)
- **Confluence**: `output/confluence/` - Downloaded Confluence pages (html)

## Configuration

### Environment Variables (.env)
```env
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your.email@example.com
JIRA_API_TOKEN=your_api_token
```

### Multi-Project Configuration (config.json)
```json
{
  "projects": [
    {
      "name": "Project Name",
      "key": "PROJ",
      "board_id": "123",
      "enabled": true,
      "description": "Project description"
    }
  ],
  "settings": {
    "aggregate_reports": true,
    "default_max_results": 200
  }
}
```

## Development

### Adding New Features

1. **Client APIs**: Add to `src/clients/`
2. **Report Types**: Add to `src/generators/`
3. **Report Formatting**: Modify formatting methods in generators for Agent optimization

### Imports

Use relative imports within the `src/` package:
```python
from ..config import Config
from ..clients.jira_client import JiraClient
```

From root scripts (main.py, confluence_reader.py):
```python
from src.config import Config
from src.clients.jira_client import JiraClient
```

## Notes

- All scripts automatically create output directories if they don't exist
- Reports are optimized for AI Agent consumption with structured metadata
- The confluence_reader.py in the root is a thin wrapper around src/clients/confluence_client.py
