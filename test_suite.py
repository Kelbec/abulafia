"""
Comprehensive Test Suite for Abulafia CLI Tools
Tests all report generation, agenda creation, and Confluence reader functionality.

Run with: pytest test_suite.py -v
Or: python test_suite.py (for standalone execution)
"""

import os
import subprocess
import sys
import yaml
from pathlib import Path


class TestResults:
    """Track test results for standalone execution"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASSED: {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ FAILED: {test_name}")
        print(f"   Error: {error}")
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\n{self.failed} test(s) failed:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        print(f"{'='*60}")


# Test output directory
TEST_OUTPUT_DIR = Path("output/test_results")
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_cli_command(command, timeout=30):
    """
    Execute a CLI command and return result.
    
    Args:
        command: Command string to execute
        timeout: Timeout in seconds
    
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def validate_yaml_metadata(file_path, expected_keys=None):
    """
    Validate that a markdown file contains YAML metadata.
    Supports both frontmatter (---) and embedded code blocks (```yaml).
    
    Args:
        file_path: Path to markdown file
        expected_keys: List of required keys in YAML
    
    Returns:
        tuple: (is_valid, metadata_dict)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata = None
        
        # Check for YAML frontmatter format (---...---)
        if content.startswith('---\n'):
            parts = content.split('---\n', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                metadata = yaml.safe_load(yaml_content)
        # Check for embedded YAML code block (```yaml...```)
        elif '```yaml' in content:
            import re
            # Use regex to properly extract YAML code block
            pattern = r'```yaml\s*\n(.*?)\n```'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                yaml_content = match.group(1)
                metadata = yaml.safe_load(yaml_content)
            else:
                return False, None
        else:
            return False, None
        
        if metadata is None:
            return False, None
        
        # Validate expected keys
        if expected_keys:
            for key in expected_keys:
                if key not in metadata:
                    return False, metadata
        
        return True, metadata
    except Exception as e:
        return False, None


def file_contains_text(file_path, search_text):
    """Check if file contains specific text"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return search_text in content
    except Exception:
        return False


# ============================================================================
# TEST CASES
# ============================================================================

def test_jira_connection():
    """Test 1: Verify Jira connection"""
    print("\n🔍 Testing Jira connection...")
    returncode, stdout, stderr = run_cli_command("python main.py test-connection")
    
    assert returncode == 0, f"Command failed with code {returncode}: {stderr}"
    assert "Connected successfully" in stdout in stdout, \
        f"Expected connection success message, got: {stdout}"


def test_agenda_markdown():
    """Test 2: Generate agenda in markdown format"""
    print("\n🔍 Testing agenda generation (markdown)...")
    output_file = TEST_OUTPUT_DIR / "test_agenda.md"
    
    returncode, stdout, stderr = run_cli_command(
        f'python main.py agenda --format md --output "{output_file}"'
    )
    
    assert returncode == 0, f"Command failed: {stderr}"
    assert output_file.exists(), f"Output file not created: {output_file}"
    
    # Validate YAML metadata
    is_valid, metadata = validate_yaml_metadata(
        output_file,
        expected_keys=['report_type', 'total_assigned']
    )
    assert is_valid, "YAML metadata missing or invalid"
    assert metadata['report_type'] == 'weekly_agenda', "Wrong report type in metadata"
    
    # Check for key sections
    assert file_contains_text(output_file, "This Week's Focus"), \
        "Missing 'This Week's Focus' section"


def test_agenda_marp():
    """Test 3: Generate agenda in Marp presentation format"""
    print("\n🔍 Testing agenda generation (Marp)...")
    output_file = TEST_OUTPUT_DIR / "test_agenda_presentation.md"
    
    returncode, stdout, stderr = run_cli_command(
        f'python main.py agenda --format marp --output "{output_file}"'
    )
    
    assert returncode == 0, f"Command failed: {stderr}"
    assert output_file.exists(), f"Output file not created: {output_file}"
    
    # Validate Marp frontmatter
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'marp: true' in content, "Missing Marp frontmatter"
    assert '# 📅 Weekly Agenda' in content, "Missing agenda title"
    assert '---' in content, "Missing slide separators"


def test_team_report_markdown():
    """Test 4: Generate team report in markdown format"""
    print("\n🔍 Testing team report generation (markdown)...")
    output_file = TEST_OUTPUT_DIR / "test_team_report.md"
    
    returncode, stdout, stderr = run_cli_command(
        f'python main.py team-report --format md --output "{output_file}"'
    )
    
    assert returncode == 0, f"Command failed: {stderr}"
    assert output_file.exists(), f"Output file not created: {output_file}"
    
    # Validate YAML metadata
    is_valid, metadata = validate_yaml_metadata(
        output_file,
        expected_keys=['report_type', 'total_members', 'total_issues']
    )
    assert is_valid, "YAML metadata missing or invalid"
    assert metadata['report_type'] == 'team_activity', "Wrong report type"
    
    # Check for key sections
    assert file_contains_text(output_file, "Key Insights & Recommended Actions"), \
        "Missing 'Key Insights & Recommended Actions' section"
    assert file_contains_text(output_file, "Team Performance Overview"), \
        "Missing team overview section"


def test_team_report_text():
    """Test 5: Generate team report in text format"""
    print("\n🔍 Testing team report generation (text)...")
    output_file = TEST_OUTPUT_DIR / "test_team_report.txt"
    
    returncode, stdout, stderr = run_cli_command(
        f'python main.py team-report --format text --output "{output_file}"'
    )
    
    assert returncode == 0, f"Command failed: {stderr}"
    assert output_file.exists(), f"Output file not created: {output_file}"
    
    # Validate content
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "TEAM ACTIVITY REPORT" in content or "Team Activity Report" in content, \
        "Missing report title"


def test_historical_report():
    """Test 6: Generate historical report"""
    print("\n🔍 Testing historical report generation...")
    output_file = TEST_OUTPUT_DIR / "test_historical_report.md"
    
    returncode, stdout, stderr = run_cli_command(
        f'python main.py historical-report --period last_week --format md --output "{output_file}"'
    )
    
    assert returncode == 0, f"Command failed: {stderr}"
    assert output_file.exists(), f"Output file not created: {output_file}"
    
    # Historical reports don't use YAML frontmatter, check for period in content
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "Historical Activity Report" in content or "Last Week" in content, \
        "Missing historical report title"
    assert "Period:" in content or "Generated:" in content, \
        "Missing period information"


def test_assigned_issues():
    """Test 7: List assigned issues"""
    print("\n🔍 Testing assigned issues command...")
    
    returncode, stdout, stderr = run_cli_command("python main.py assigned-issues")
    
    assert returncode == 0, f"Command failed: {stderr}"
    # Should output some issues or message about no issues
    assert len(stdout) > 0, "No output from assigned-issues command"


def test_in_progress():
    """Test 8: List in-progress issues"""
    print("\n🔍 Testing in-progress issues command...")
    
    returncode, stdout, stderr = run_cli_command("python main.py in-progress")
    
    assert returncode == 0, f"Command failed: {stderr}"
    # Should output some issues or message about no issues
    assert len(stdout) > 0, "No output from in-progress command"


def test_confluence_reader_help():
    """Test 9: Confluence reader help"""
    print("\n🔍 Testing Confluence reader (help)...")
    
    returncode, stdout, stderr = run_cli_command("python confluence_reader.py --help")
    
    assert returncode == 0, f"Command failed: {stderr}"
    assert "Fetch Confluence page" in stdout or "page_title" in stdout, \
        "Help text missing expected content"


def test_all_output_formats():
    """Test 10: Verify all format options work"""
    print("\n🔍 Testing all output format variations...")
    
    # Only test valid formats: text, md, marp (not 'markdown')
    formats = ['text', 'md', 'marp']
    for fmt in formats:
        output_file = TEST_OUTPUT_DIR / f"test_format_{fmt}.md"
        returncode, stdout, stderr = run_cli_command(
            f'python main.py team-report --format {fmt} --output "{output_file}"'
        )
        assert returncode == 0, f"Format {fmt} failed: {stderr}"


# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

def run_standalone_tests():
    """Run tests without pytest for standalone execution"""
    results = TestResults()
    
    print("=" * 60)
    print("🧪 Abulafia CLI Test Suite")
    print("=" * 60)
    
    tests = [
        ("Jira Connection", test_jira_connection),
        ("Agenda (Markdown)", test_agenda_markdown),
        ("Agenda (Marp)", test_agenda_marp),
        ("Team Report (Markdown)", test_team_report_markdown),
        ("Team Report (Text)", test_team_report_text),
        ("Historical Report", test_historical_report),
        ("Assigned Issues", test_assigned_issues),
        ("In-Progress Issues", test_in_progress),
        ("Confluence Reader Help", test_confluence_reader_help),
        ("All Output Formats", test_all_output_formats),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.add_pass(test_name)
        except AssertionError as e:
            results.add_fail(test_name, str(e))
        except Exception as e:
            results.add_fail(test_name, f"Unexpected error: {str(e)}")
    
    results.print_summary()
    return results.failed == 0


if __name__ == "__main__":
    # Check if pytest is available
    try:
        import pytest
        print("Running with pytest...\n")
        sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
    except ImportError:
        print("pytest not found, running standalone tests...\n")
        success = run_standalone_tests()
        sys.exit(0 if success else 1)
