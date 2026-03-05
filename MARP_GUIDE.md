# 📊 Marp Presentation Export Guide

## What is Marp?

**Marp** (Markdown Presentation Ecosystem) is a tool that converts markdown files into beautiful presentations. With Abulafia, you can now export any report as a Marp presentation!

## 🎯 Features

Your exported Marp presentations include:

- **📽️ Title Slide** - Professional intro with report name and date range
- **📊 Summary Slides** - Key metrics and overview data
- **📈 Data Visualizations** - Status distributions, team performance, etc.
- **⚠️ Alert Slides** - Bottleneck detection and risk analysis (for team reports)
- **👥 Team Performance** - Individual member highlights and rankings
- **💡 Recommendations** - Action items and next steps

## 🚀 How to Use

### Step 1: Export Report as Marp

1. Run `python main.py`
2. Select **Option 9** (Export Reports)
3. Choose your report type:
   - Personal Weekly Agenda
   - Team Report
   - Historical Report
4. Select format **3. Marp Presentation (.md)**
5. File will be saved as `*_presentation.md`

### Step 2: View/Convert the Presentation

#### Option A: VS Code (Easiest)

1. Install **"Marp for VS Code"** extension
2. Open the `*_presentation.md` file in VS Code
3. Click the **"Open Preview"** button (top right)
4. View your slides in preview mode!

**Export options:**
- Click **"Export Slide Deck"** button
- Choose format: PDF, PPTX, HTML
- Present directly from VS Code

#### Option B: Marp CLI

1. Install Marp CLI:
   ```bash
   npm install -g @marp-team/marp-cli
   ```

2. Convert to PDF:
   ```bash
   marp agenda_2026-03-02_presentation.md --pdf
   ```

3. Convert to PowerPoint:
   ```bash
   marp agenda_2026-03-02_presentation.md --pptx
   ```

4. Convert to HTML:
   ```bash
   marp agenda_2026-03-02_presentation.md --html
   ```

5. Watch mode (auto-update):
   ```bash
   marp -w agenda_2026-03-02_presentation.md
   ```

## 📋 Example Presentation Structure

### Personal Weekly Agenda Presentation

1. **Title Slide** - Week range and agenda title
2. **Overview** - Total assigned, in progress, due items
3. **In Progress** - Current work with details
4. **Due This Week** - Upcoming deadlines
5. **Current Sprint** - Sprint backlog items
6. **Top Priorities** - Highest priority tasks
7. **Summary** - Focus items and execution plan

### Team Report Presentation

1. **Title Slide** - Team size and total issues
2. **Projects** - Multi-project breakdown (if aggregate)
3. **Overview** - Key metrics and averages
4. **Status Distribution** - Visual breakdown by status
5. **Bottleneck Alerts** - Risks and issues
6. **Stale Issues** - Items needing attention
7. **Top Performers** - Team leaderboard
8. **Recommendations** - Action items

### Historical Report Presentation

1. **Title Slide** - Period and date range
2. **Key Metrics** - Completed, updated, created counts
3. **Team Productivity** - Leaderboard with medals
4. **Completed Highlights** - Top finished items
5. **Velocity Analysis** - Team performance metrics
6. **Summary** - Period recap

## 🎨 Customization

### Themes

Marp supports different themes. Edit the frontmatter in your presentation file:

```markdown
---
marp: true
theme: default  # Change to: gaia, uncover, etc.
paginate: true
---
```

### Available Themes:
- `default` - Clean professional look
- `gaia` - Colorful and modern
- `uncover` - Minimalist design

### Custom Styles

Add custom CSS in the presentation file:

```markdown
---
marp: true
theme: default
style: |
  section {
    background-color: #f5f5f5;
  }
  h1 {
    color: #2563eb;
  }
---
```

## 💡 Tips & Tricks

### 1. Lead (Center) Slides
Use for title and summary slides:
```markdown
<!-- _class: lead -->
# Centered Title
```

### 2. Custom Footer/Header
Already set in the presentation:
```markdown
header: '📅 Weekly Agenda'
footer: '2026-03-02 - 2026-03-08'
```

### 3. Speaker Notes
Add notes that won't appear in slides:
```markdown
---
# My Slide

<!-- This is a speaker note -->
Content here...
```

### 4. Split Columns
Create side-by-side content:
```markdown
<div style="display: flex;">
<div style="flex: 1;">
Left column
</div>
<div style="flex: 1;">
Right column
</div>
</div>
```

## 📱 Presenting

### From VS Code
1. Open Marp preview
2. Press **F5** or click "Start Slideshow"
3. Use arrow keys to navigate
4. Press **Esc** to exit

### From HTML Export
1. Export to HTML: `marp file.md --html`
2. Open in browser
3. Use arrow keys or click to navigate
4. Press **F** for fullscreen

### From PDF/PPTX
1. Export to PDF or PowerPoint
2. Open in respective application
3. Present normally

## 🔧 Troubleshooting

### "Marp not found"
Install Marp CLI:
```bash
npm install -g @marp-team/marp-cli
```

### VS Code extension not working
1. Reload VS Code window
2. Check extension is enabled
3. Try opening preview with **Ctrl+Shift+P** → "Marp: Open Preview"

### Images not showing
Make sure image paths are relative to the markdown file location.

### Emojis not rendering
Ensure your system/font supports emoji rendering. Most modern systems do by default.

## 📚 Resources

- **Marp Official Site**: https://marp.app/
- **Marp CLI Docs**: https://github.com/marp-team/marp-cli
- **VS Code Extension**: https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode
- **Theme Gallery**: https://github.com/marp-team/marp-core/tree/main/themes

## 🎬 Example Workflow

1. Generate weekly agenda: `python main.py` → Option 1
2. Export as Marp: Option 9 → Report Type 1 → Format 3
3. Open in VS Code with Marp extension
4. Preview the presentation
5. Export to PDF for meeting
6. Share PDF with team!

---

**Happy Presenting! 🎉**

Your reports are now ready for any meeting, review, or presentation context!
