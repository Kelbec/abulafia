# Multi-Project Support - Quick Start Guide

## 🎉 What's New?

Abulafia tool now supports **multiple Jira projects** and can generate **aggregate reports** across all your Jira spaces!

## 📂 Configuration Files

### 1. `.env` (Credentials - Keep Secret!)
Stores your Jira credentials:
```env
JIRA_SERVER=https://your-server.atlassian.net
JIRA_EMAIL=your-email-here
JIRA_API_TOKEN=your-token-here
```

### 2. `config.json` (NEW - Project Settings)
Define multiple Jira projects:
```json
{
  "projects": [
    {
      "name": "New project",
      "key": "PRJ",
      "board_id": "New project",
      "enabled": true,
      "description": "Main project board"
    },
    {
      "name": "Another Project",
      "key": "PROJ2",
      "board_id": "123",
      "enabled": true,
      "description": "Second project"
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

## 🚀 How to Add More Projects

1. **Open `config.json`** in your editor

2. **Add a new project** to the `projects` array:
```json
{
  "name": "My New Project",
  "key": "NEWPROJ",
  "board_id": "456",
  "enabled": true,
  "description": "Description here"
}
```

3. **Find your project key:**
   - Go to your Jira project
   - Look at the issue keys (e.g., "PRJ-123" → "PRJ" is the key)

4. **Find your board ID (optional):**
   - Go to your Jira board
   - Look at the URL: `.../board/123` → "123" is the board ID
   - Or use the board name like "New project"

## 📊 Using Multi-Project Reports

When you run `python main.py` and select:

### Option 7: Team Report
You'll see:
```
📦 Available Projects:
  1. New project (PRJ)
  2. Infrastructure (INFRA)
  3. Aggregate Report (All Projects)

Select project or aggregate (1-3): 
```

- **Select 1 or 2**: Single project report
- **Select 3**: Aggregate report across ALL projects

### Option 8: Historical Report
Same selection, then choose your time period:
- Last Week
- Last Month
- Current Week
- Current Month

## ✨ What's New in Aggregate Reports?

### Team Report Shows:
- 🔗 **Projects Included** - Table showing all projects in the report
- 📊 **Cross-Project Metrics** - Total issues across all spaces
- 👥 **Unified Team View** - All team members from all projects
- ⚠️ **Bottleneck Detection** - Issues across all your Jira spaces
- 🤖 **LLM SumPRJy** - AI-ready analysis of all projects

### Historical Report Shows:
- 📈 Combined activity from all projects
- 🏆 Team productivity across multiple spaces
- ✅ All completed/updated/created issues

## 🎯 Single Project Mode (Legacy)

If you don't want multi-project features:
1. Keep only ONE project in `config.json` with `enabled: true`
2. OR delete `config.json` entirely (system will use `.env` values)

## 🔒 Security Notes

- ✅ `config.json` is added to `.gitignore`
- ✅ Only contains project keys, NOT credentials
- ✅ Credentials stay in `.env` (already in .gitignore)
- ⚠️  Don't commit `config.json` to public repos if it contains sensitive project info

## 📝 Example Workflow

### Current Setup
Your `config.json` currently has:
- 1 project: New project (PRJ)

### To Add More Projects:
1. Edit `config.json`
2. Copy the existing project block
3. Change the name, key, and board_id
4. Set `enabled: true`
5. Save and run `python main.py`

### Example with 3 Projects:
```json
{
  "projects": [
    {
      "name": "New project",
      "key": "PRJ",
      "board_id": "New project",
      "enabled": true,
      "description": "Main development"
    },
    {
      "name": "DevOps",
      "key": "DEVOPS",
      "board_id": "2",
      "enabled": true,
      "description": "Infrastructure work"
    },
    {
      "name": "Support",
      "key": "SUP",
      "board_id": "3",
      "enabled": false,
      "description": "Customer support (disabled)"
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

## 🛠️ Troubleshooting

### "Could not fetch issues from project XXX"
- Check the project key is correct
- Verify you have access to that project in Jira
- The system will continue with other projects

### "No projects found"
- Make sure `config.json` exists
- Check at least one project has `enabled: true`
- Or use legacy mode (delete config.json)

### Reports look the same
- Check you're selecting "Aggregate Report" option
- Verify config.json has multiple enabled projects

## 📚 Files Reference

| File | Purpose | Contains |
|------|---------|----------|
| `.env` | Credentials | API tokens (SECRET) |
| `config.json` | Projects | Project keys and settings |
| `config.json.example` | Template | Example configuration |
| `.gitignore` | Git exclusions | Blocks .env and config.json |

---

**Ready to try?** Run `python main.py` and select option 7 or 8!
