import typer
from github import GithubException
from rich.console import Console

from coding_agent.agents import CodeAgent, ReviewerAgent
from coding_agent.config import get_settings
from coding_agent.repo_manager import RepoManager

app = typer.Typer(
    name="code-agent",
    help="Агент для автоматизации разработки на GitHub",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
repo_manager = RepoManager()


@app.command()
def run(
    issue: int = typer.Option(..., "--issue", "-i", help="Номер Issue"),
    repo: str = typer.Option(..., "--repo", "-r", help="Репозиторий (owner/repo)"),
    token: str | None = typer.Option(None, "--token", "-t", help="GitHub токен"),
):
    """Сгенерировать код по Issue и создать PR."""
    settings = get_settings()
    settings.github_repository = repo
    if token:
        settings.github_token = token

    repo_url = f"https://github.com/{repo}.git"
    repo_path = repo_manager.clone(repo_url, settings.github_token)
    console.print(f"[dim]Склонировано в {repo_path}[/dim]")

    try:
        agent = CodeAgent(settings, repo_path)
        agent.run(issue)
    except GithubException as e:
        if e.status == 404:
            console.print(f"[red]Issue #{issue} не найден в {repo}[/red]")
        else:
            console.print(f"[red]Ошибка GitHub: {e.data.get('message', str(e))}[/red]")
        raise typer.Exit(1)
    finally:
        repo_manager.cleanup(repo_path)
        console.print("[dim]Временная папка удалена[/dim]")


@app.command()
def review(
    pr: int = typer.Option(..., "--pr", "-p", help="Номер PR"),
    repo: str = typer.Option(..., "--repo", "-r", help="Репозиторий (owner/repo)"),
    token: str | None = typer.Option(None, "--token", "-t", help="GitHub токен"),
):
    """Проверить PR и дать обратную связь."""
    settings = get_settings()
    settings.github_repository = repo
    if token:
        settings.github_token = token

    try:
        agent = ReviewerAgent(settings)
        agent.review(pr)
    except GithubException as e:
        if e.status == 404:
            console.print(f"[red]PR #{pr} не найден в {repo}[/red]")
        else:
            console.print(f"[red]Ошибка GitHub: {e.data.get('message', str(e))}[/red]")
        raise typer.Exit(1)


@app.command()
def fix(
    pr: int = typer.Option(..., "--pr", "-p", help="Номер PR"),
    repo: str = typer.Option(..., "--repo", "-r", help="Репозиторий (owner/repo)"),
    token: str | None = typer.Option(None, "--token", "-t", help="GitHub токен"),
):
    """Исправить код по замечаниям из ревью."""
    settings = get_settings()
    settings.github_repository = repo
    if token:
        settings.github_token = token

    repo_url = f"https://github.com/{repo}.git"
    repo_path = repo_manager.clone(repo_url, settings.github_token)
    console.print(f"[dim]Склонировано в {repo_path}[/dim]")

    try:
        agent = CodeAgent(settings, repo_path)
        agent.fix(pr)
    except GithubException as e:
        if e.status == 404:
            console.print(f"[red]PR #{pr} не найден в {repo}[/red]")
        else:
            console.print(f"[red]Ошибка GitHub: {e.data.get('message', str(e))}[/red]")
        raise typer.Exit(1)
    finally:
        repo_manager.cleanup(repo_path)
        console.print("[dim]Временная папка удалена[/dim]")


if __name__ == "__main__":
    app()
