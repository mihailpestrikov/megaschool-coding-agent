from pydantic import BaseModel


class FileChange(BaseModel):
    """Изменение одного файла."""

    path: str
    action: str
    content: str = ""


class CodeGenerationResult(BaseModel):
    """Результат генерации кода."""

    analysis: str
    files: list[FileChange]
    commit_message: str
    validation_commands: list[str] = []


class ReviewComment(BaseModel):
    """Замечание к коду."""

    file: str
    line: int | None = None
    problem: str
    suggestion: str


class ReviewResult(BaseModel):
    """Результат ревью PR."""

    approved: bool
    summary: str
    comments: list[ReviewComment] = []
