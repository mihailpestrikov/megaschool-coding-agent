import typer
from rich.console import Console

from coding_agent.config import get_settings
from coding_agent.agents import CodeAgent

app = typer.Typer(
    name="code-agent",
    help="Агент для автоматизации разработки на GitHub",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def run(
    issue: int = typer.Option(..., "--issue", "-i", help="Номер Issue для реализации"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="Репозиторий (owner/repo)"),
):
    """Сгенерировать код по Issue и создать PR."""
    try:
        settings = get_settings()
        if repo:
            settings.github_repository = repo

        agent = CodeAgent(settings)
        agent.run(issue)
    except Exception as e:
        console.print(f"[red]Ошибка: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def review(
    pr: int = typer.Option(..., "--pr", "-p", help="Номер PR для ревью"),
):
    """Проверить PR и дать обратную связь."""
    console.print(f"[blue]Проверяю PR #{pr}...[/blue]")
    # TODO: реализовать в следующем шаге


@app.command()
def fix(
    pr: int = typer.Option(..., "--pr", "-p", help="Номер PR для исправления"),
):
    """Исправить код по замечаниям из ревью."""
    console.print(f"[blue]Исправляю PR #{pr}...[/blue]")
    # TODO: реализовать в следующем шаге


if __name__ == "__main__":
    app()
