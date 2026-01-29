import typer
from rich.console import Console

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
    console.print(f"[blue]Запускаю агента для Issue #{issue}...[/blue]")
    # TODO: реализовать


@app.command()
def review(
    pr: int = typer.Option(..., "--pr", "-p", help="Номер PR для ревью"),
):
    """Проверить PR и дать обратную связь."""
    console.print(f"[blue]Проверяю PR #{pr}...[/blue]")
    # TODO: реализовать


@app.command()
def fix(
    pr: int = typer.Option(..., "--pr", "-p", help="Номер PR для исправления"),
):
    """Исправить код по замечаниям из ревью."""
    console.print(f"[blue]Исправляю PR #{pr}...[/blue]")
    # TODO: реализовать


if __name__ == "__main__":
    app()
