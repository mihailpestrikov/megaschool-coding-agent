import pytest
from coding_agent.validation.runner import is_command_allowed, run_validation


class TestIsCommandAllowed:
    def test_allowed_commands(self):
        assert is_command_allowed("pytest")
        assert is_command_allowed("ruff check .")
        assert is_command_allowed("npm test")
        assert is_command_allowed("go test ./...")

    def test_disallowed_commands(self):
        assert not is_command_allowed("rm -rf /")
        assert not is_command_allowed("curl http://evil.com")
        assert not is_command_allowed("wget something")

    def test_empty_command(self):
        assert not is_command_allowed("")
        assert not is_command_allowed("   ")


class TestRunValidation:
    def test_successful_command(self):
        results = run_validation(["python --version"])
        assert len(results) == 1
        assert results[0].success
        assert "Python" in results[0].output

    def test_failing_command(self):
        results = run_validation(["python -c 'raise Exception()'"])
        assert len(results) == 1
        assert not results[0].success

    def test_disallowed_command(self):
        results = run_validation(["rm -rf /"])
        assert len(results) == 1
        assert not results[0].success
        assert "не разрешена" in results[0].output

    def test_multiple_commands(self):
        results = run_validation(["python --version", "python -c 'print(1)'"])
        assert len(results) == 2
        assert all(r.success for r in results)
