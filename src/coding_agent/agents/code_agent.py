from pathlib import Path
from git import Repo
from rich.console import Console

from coding_agent.config import Settings
from coding_agent.llm import LLMClient
from coding_agent.github import GitHubClient
from coding_agent.context import ContextCollector

console = Console()


class CodeAgent:
    def __init__(self, settings: Settings, repo_path: str | Path = "."):
        self.settings = settings
        self.repo_path = Path(repo_path)
        self.llm = LLMClient(settings)
        self.github = GitHubClient(settings.github_token, settings.github_repository)
        self.context_collector = ContextCollector(repo_path)
        self.git_repo = Repo(repo_path)

    def run(self, issue_number: int) -> str:
        """Реализовать Issue и создать PR. Возвращает URL созданного PR."""

        # 1. Получаем Issue
        console.print(f"[blue]Читаю Issue #{issue_number}...[/blue]")
        issue = self.github.get_issue(issue_number)
        issue_text = f"{issue.title}\n\n{issue.body or ''}"

        # 2. Собираем контекст репозитория
        console.print("[blue]Собираю контекст репозитория...[/blue]")
        context = self.context_collector.collect(issue_text)

        # 3. Генерируем код через LLM
        console.print("[blue]Генерирую код...[/blue]")
        result = self.llm.generate_code(issue.title, issue.body or "", context)
        console.print(f"[dim]Анализ: {result.analysis}[/dim]")

        # 4. Создаём веткуи
        branch_name = f"agent/issue-{issue_number}"
        console.print(f"[blue]Создаю ветку {branch_name}...[/blue]")
        self._create_branch(branch_name)

        # 5. Применяем изменения
        console.print(f"[blue]Применяю изменения ({len(result.files)} файлов)...[/blue]")
        changed_files = []
        for file_change in result.files:
            self._apply_file_change(file_change)
            changed_files.append(file_change.path)
            console.print(f"  [green]{file_change.action}:[/green] {file_change.path}")

        console.print("[blue]Коммичу и пушу...[/blue]")
        self._commit_and_push(branch_name, result.commit_message, changed_files)

        console.print("[blue]Создаю Pull Request...[/blue]")
        pr_body = self._make_pr_body(issue_number, result.analysis)
        pr = self.github.create_pr(
            title=f"[#{issue_number}] {issue.title}",
            body=pr_body,
            branch=branch_name,
        )

        console.print(f"[green]Готово! PR создан: {pr.html_url}[/green]")
        return pr.html_url

    def _create_branch(self, branch_name: str):
        """Создать новую ветку и переключиться на неё."""
        if branch_name in self.git_repo.heads:
            self.git_repo.delete_head(branch_name, force=True)

        base = self.git_repo.active_branch
        new_branch = self.git_repo.create_head(branch_name, base)
        new_branch.checkout()

    def _apply_file_change(self, file_change):
        filepath = self.repo_path / file_change.path

        if file_change.action == "delete":
            if filepath.exists():
                filepath.unlink()
        else:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(file_change.content, encoding="utf-8")

    def _commit_and_push(self, branch_name: str, message: str, files: list[str]):
        self.git_repo.index.add(files)
        self.git_repo.index.commit(message)
        origin = self.git_repo.remote("origin")
        origin.push(branch_name, set_upstream=True)

    def _make_pr_body(self, issue_number: int, analysis: str) -> str:
        return f"""Closes #{issue_number}

## Что сделано
{analysis}

---
<!-- AGENT: iteration=1, max={self.settings.max_iterations}, issue={issue_number} -->
"""
