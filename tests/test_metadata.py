import pytest
from coding_agent.agents.code_agent import CodeAgent


class TestParseMetadata:
    def parse(self, text):
        return CodeAgent._parse_metadata(None, text)

    def test_valid_metadata(self):
        text = "Some text\n<!-- AGENT: iteration=2, max=5, issue=42 -->\nMore text"
        result = self.parse(text)
        assert result == {"iteration": 2, "max": 5, "issue": 42}

    def test_first_iteration(self):
        text = "<!-- AGENT: iteration=1, max=5, issue=1 -->"
        result = self.parse(text)
        assert result["iteration"] == 1

    def test_no_metadata(self):
        text = "Just a regular PR body without metadata"
        result = self.parse(text)
        assert result is None

    def test_partial_metadata(self):
        text = "<!-- AGENT: iteration=1 -->"
        result = self.parse(text)
        assert result is None

    def test_metadata_in_pr_body(self):
        text = """Closes #42

## Что сделано
Добавил функцию

---
<!-- AGENT: iteration=1, max=5, issue=42 -->
"""
        result = self.parse(text)
        assert result == {"iteration": 1, "max": 5, "issue": 42}
