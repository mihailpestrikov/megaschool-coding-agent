import pytest
from pydantic import ValidationError
from coding_agent.llm.schemas import FileChange, CodeGenerationResult, ReviewResult, ReviewComment


class TestFileChange:
    def test_valid(self):
        fc = FileChange(path="src/main.py", action="create", content="print(1)")
        assert fc.path == "src/main.py"
        assert fc.action == "create"

    def test_empty_content_allowed(self):
        fc = FileChange(path="file.py", action="delete")
        assert fc.content == ""

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            FileChange(content="test")


class TestCodeGenerationResult:
    def test_valid(self):
        result = CodeGenerationResult(
            analysis="Добавил функцию",
            files=[FileChange(path="a.py", action="create", content="x=1")],
            commit_message="feat: add function",
        )
        assert len(result.files) == 1


class TestReviewResult:
    def test_approved(self):
        review = ReviewResult(approved=True, summary="Всё хорошо")
        assert review.approved
        assert review.comments == []

    def test_with_comments(self):
        review = ReviewResult(
            approved=False,
            summary="Есть проблемы",
            comments=[
                ReviewComment(file="main.py", line=10, problem="баг", suggestion="исправь"),
            ],
        )
        assert len(review.comments) == 1
        assert review.comments[0].line == 10
