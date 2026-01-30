import hashlib
import hmac
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from rich.console import Console

from coding_agent.agents.code_agent import CodeAgent
from coding_agent.agents.reviewer import ReviewerAgent
from coding_agent.config import Settings
from coding_agent.github.app_auth import GitHubAppAuth
from coding_agent.repo_manager import RepoManager

console = Console()

settings = Settings()
app_auth = GitHubAppAuth(
    app_id=os.getenv("GITHUB_APP_ID", ""),
    private_key=os.getenv("GITHUB_PRIVATE_KEY", "").replace("\\n", "\n"),
)
repo_manager = RepoManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    console.print("[green]Сервер запущен[/green]")
    yield
    console.print("[yellow]Сервер остановлен[/yellow]")


app = FastAPI(lifespan=lifespan)


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return True
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    if not verify_signature(payload, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event")
    data = await request.json()

    if event == "issues" and data.get("action") == "labeled":
        if data["label"]["name"] == "agent":
            await handle_issue(data)

    if event == "pull_request" and data.get("action") in ["opened", "synchronize"]:
        await handle_pr_review(data)

    if event == "pull_request_review":
        if data["review"]["state"] == "changes_requested":
            await handle_fix(data)

    return {"status": "ok"}


async def handle_issue(data: dict):
    installation_id = data["installation"]["id"]
    repo_full_name = data["repository"]["full_name"]
    repo_url = data["repository"]["clone_url"]
    issue_number = data["issue"]["number"]

    console.print(f"[blue]Issue #{issue_number} в {repo_full_name}[/blue]")

    token = app_auth.get_installation_token(installation_id)
    repo_path = repo_manager.clone(repo_url, token)

    try:
        agent_settings = Settings()
        agent_settings.github_token = token
        agent_settings.github_repository = repo_full_name

        agent = CodeAgent(agent_settings, repo_path)
        pr_url = agent.run(issue_number)
        console.print(f"[green]PR создан: {pr_url}[/green]")
    finally:
        repo_manager.cleanup(repo_path)


async def handle_pr_review(data: dict):
    installation_id = data["installation"]["id"]
    repo_full_name = data["repository"]["full_name"]
    pr_number = data["pull_request"]["number"]

    console.print(f"[blue]Ревью PR #{pr_number} в {repo_full_name}[/blue]")

    token = app_auth.get_installation_token(installation_id)

    agent_settings = Settings()
    agent_settings.github_token = token
    agent_settings.github_repository = repo_full_name

    reviewer = ReviewerAgent(agent_settings)
    result = reviewer.review(pr_number)
    console.print(f"[green]Ревью: {'approved' if result.approved else 'changes requested'}[/green]")


async def handle_fix(data: dict):
    installation_id = data["installation"]["id"]
    repo_full_name = data["repository"]["full_name"]
    repo_url = data["repository"]["clone_url"]
    pr_number = data["pull_request"]["number"]

    console.print(f"[blue]Fix PR #{pr_number} в {repo_full_name}[/blue]")

    token = app_auth.get_installation_token(installation_id)
    repo_path = repo_manager.clone(repo_url, token)

    try:
        agent_settings = Settings()
        agent_settings.github_token = token
        agent_settings.github_repository = repo_full_name

        agent = CodeAgent(agent_settings, repo_path)
        agent.fix(pr_number)
    finally:
        repo_manager.cleanup(repo_path)


@app.get("/health")
async def health():
    return {"status": "healthy"}
