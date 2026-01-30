import pytest
import tempfile
from pathlib import Path
from coding_agent.context.collector import ContextCollector


@pytest.fixture
def temp_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "README.md").write_text("# Test Project")
        (root / "pyproject.toml").write_text("[project]\nname = 'test'")
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("def hello(): pass")
        (root / "src" / "utils.py").write_text("def helper(): pass")
        yield root


class TestContextCollector:
    def test_collect_basic(self, temp_repo):
        collector = ContextCollector(temp_repo)
        context = collector.collect("test issue")
        assert "README.md" in context
        assert "Test Project" in context

    def test_includes_pyproject(self, temp_repo):
        collector = ContextCollector(temp_repo)
        context = collector.collect("test")
        assert "pyproject.toml" in context

    def test_finds_relevant_files(self, temp_repo):
        collector = ContextCollector(temp_repo)
        context = collector.collect("need to fix hello function")
        assert "main.py" in context

    def test_respects_size_limit(self, temp_repo):
        big_file = temp_repo / "big.py"
        big_file.write_text("x = 1\n" * 100000)

        collector = ContextCollector(temp_repo)
        context = collector.collect("test")
        assert len(context) < 60000

    def test_ignores_hidden_dirs(self, temp_repo):
        (temp_repo / ".git").mkdir()
        (temp_repo / ".git" / "config").write_text("secret")

        collector = ContextCollector(temp_repo)
        context = collector.collect("test")
        assert "secret" not in context
