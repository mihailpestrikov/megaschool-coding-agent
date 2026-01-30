from pathlib import Path

from git import Repo
from rich.console import Console

from coding_agent.config import Settings
from coding_agent.context import ContextCollector
from coding_agent.github import GitHubClient
from coding_agent.llm import LLMClient
from coding_agent.validation import run_validation

console = Console()

MAX_VALIDATION_RETRIES = 3


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

        # 6. Локальная валидация
        if result.validation_commands:
            result = self._run_validation_loop(
                result, issue.title, issue.body or "", context
            )

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

    def fix(self, pr_number: int) -> bool:
        """Исправить код по замечаниям из ревью. Возвращает True если успешно."""
        import re

        # 1. Получаем PR и парсим metadata
        console.print(f"[blue]Читаю PR #{pr_number}...[/blue]")
        pr = self.github.get_pr(pr_number)
        metadata = self._parse_metadata(pr.body or "")

        if not metadata:
            console.print("[red]Не найдены метаданные агента в PR[/red]")
            return False

        issue_number = metadata["issue"]
        iteration = metadata["iteration"]
        max_iterations = metadata["max"]

        # 2. Проверяем лимит итераций
        if iteration >= max_iterations:
            console.print(f"[red]Достигнут лимит итераций ({max_iterations})[/red]")
            self.github.add_comment(pr_number, "Лимит итераций. Требуется проверка.")
            self.github.add_label(pr_number, "needs-human-review")
            return False

        # 3. Получаем Issue и feedback
        console.print(f"[blue]Читаю Issue #{issue_number}...[/blue]")
        issue = self.github.get_issue(issue_number)

        console.print("[blue]Собираю замечания из ревью...[/blue]")
        feedback = self._get_review_feedback(pr)

        # 4. Собираем контекст
        console.print("[blue]Собираю контекст...[/blue]")
        issue_text = f"{issue.title}\n\n{issue.body or ''}"
        context = self.context_collector.collect(issue_text)

        # 5. Генерируем исправления
        console.print("[blue]Генерирую исправления...[/blue]")
        result = self.llm.generate_fix(feedback, issue.title, issue.body or "", context)
        console.print(f"[dim]Анализ: {result.analysis}[/dim]")

        # 6. Переключаемся на ветку PR
        branch_name = pr.head.ref
        console.print(f"[blue]Переключаюсь на ветку {branch_name}...[/blue]")
        self._checkout_branch(branch_name)

        # 7. Применяем изменения
        console.print(f"[blue]Применяю изменения ({len(result.files)} файлов)...[/blue]")
        changed_files = []
        for file_change in result.files:
            self._apply_file_change(file_change)
            changed_files.append(file_change.path)
            console.print(f"  [green]{file_change.action}:[/green] {file_change.path}")

        # 8. Коммитим и пушим
        console.print("[blue]Коммичу и пушу...[/blue]")
        commit_msg = f"fix: {result.commit_message} (iteration {iteration + 1})"
        self._commit_and_push(branch_name, commit_msg, changed_files)

        # 9. Обновляем metadata в PR
        new_body = re.sub(
            r'iteration=\d+',
            f'iteration={iteration + 1}',
            pr.body or ""
        )
        pr.edit(body=new_body)

        console.print(f"[green]Готово! Итерация {iteration + 1}/{max_iterations}[/green]")
        return True

    def _checkout_branch(self, branch_name: str):
        origin = self.git_repo.remote("origin")
        origin.fetch()

        if branch_name in self.git_repo.heads:
            self.git_repo.heads[branch_name].checkout()
        else:
            self.git_repo.create_head(branch_name, f"origin/{branch_name}").checkout()

    def _parse_metadata(self, text: str) -> dict | None:
        import re
        match = re.search(r'AGENT:\s*iteration=(\d+),\s*max=(\d+),\s*issue=(\d+)', text)
        if match:
            return {
                "iteration": int(match.group(1)),
                "max": int(match.group(2)),
                "issue": int(match.group(3)),
            }
        return None

    def _get_review_feedback(self, pr) -> str:
        reviews = list(pr.get_reviews())
        if not reviews:
            return "Нет замечаний"

        for review in reversed(reviews):
            if review.state == "CHANGES_REQUESTED":
                return review.body or "Требуются изменения (без комментария)"

        return "Нет замечаний"

    def _run_validation_loop(self, result, issue_title: str, issue_body: str, context: str):
        """Запускает валидацию и исправляет ошибки до MAX_VALIDATION_RETRIES раз."""
        for attempt in range(MAX_VALIDATION_RETRIES):
            console.print(f"[blue]Валидация (попытка {attempt + 1})...[/blue]")

            validations = run_validation(result.validation_commands, str(self.repo_path))
            failed = [v for v in validations if not v.success]

            if not failed:
                console.print("[green]Валидация пройдена[/green]")
                return result

            for v in failed:
                console.print(f"[red]✗ {v.command}[/red]")

            if attempt + 1 >= MAX_VALIDATION_RETRIES:
                console.print("[yellow]Лимит попыток, коммитим как есть[/yellow]")
                return result

            errors = "\n".join(f"$ {v.command}\n{v.output}" for v in failed)
            console.print("[blue]Исправляю ошибки...[/blue]")
            result = self.llm.generate_fix(errors, issue_title, issue_body, context)

            for file_change in result.files:
                self._apply_file_change(file_change)

        return result

    def _make_pr_body(self, issue_number: int, analysis: str) -> str:
        return f"""Closes #{issue_number}

## Что сделано
{analysis}

---
<!-- AGENT: iteration=1, max={self.settings.max_iterations}, issue={issue_number} -->
"""
