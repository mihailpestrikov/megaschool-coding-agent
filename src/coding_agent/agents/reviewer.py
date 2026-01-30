import re

from rich.console import Console

from coding_agent.config import Settings
from coding_agent.github import GitHubClient
from coding_agent.llm import LLMClient

console = Console()


class ReviewerAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMClient(settings)
        self.github = GitHubClient(settings.github_token, settings.github_repository)

    def review(self, pr_number: int) -> bool:
        """Проверить PR и оставить ревью. Возвращает True если одобрено."""

        # 1. Получаем PR и связанный Issue
        console.print(f"[blue]Читаю PR #{pr_number}...[/blue]")
        pr = self.github.get_pr(pr_number)
        issue_number = self._extract_issue_number(pr.body or "")

        if issue_number:
            issue = self.github.get_issue(issue_number)
            issue_title = issue.title
            issue_body = issue.body or ""
        else:
            issue_title = pr.title
            issue_body = pr.body or ""

        # 2. Получаем diff
        console.print("[blue]Получаю diff...[/blue]")
        diff = self.github.get_pr_diff(pr_number)

        # 3. Генерируем ревью через LLM
        console.print("[blue]Анализирую код...[/blue]")
        result = self.llm.generate_review(diff, issue_title, issue_body)

        # 5. Публикуем ревью
        console.print("[blue]Публикую ревью...[/blue]")
        review_body = f"## Результат проверки\n\n{result.summary}\n\n"
        if result.comments:
            review_body += "## Замечания\n\n"
            for c in result.comments:
                location = f"{c.file}:{c.line}" if c.line else c.file
                review_body += f"- **{location}**: {c.problem}\n  - {c.suggestion}\n\n"

        self.github.create_review(pr_number, review_body, approve=result.approved)

        if result.approved:
            console.print("[green]PR одобрен![/green]")
        else:
            console.print("[yellow]Требуются изменения[/yellow]")

        return result.approved

    def _extract_issue_number(self, text: str) -> int | None:
        match = re.search(r'(?:closes|fixes|resolves)\s*#(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        match = re.search(r'issue=(\d+)', text)
        if match:
            return int(match.group(1))

        return None
