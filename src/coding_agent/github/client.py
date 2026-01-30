from dataclasses import dataclass

from github import Github
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository


@dataclass
class CIStatus:
    success: bool
    summary: str


class GitHubClient:
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token)
        self.repo: Repository = self.github.get_repo(repo_name)

    def get_default_branch(self) -> str:
        return self.repo.default_branch

    def get_issue(self, number: int) -> Issue:
        return self.repo.get_issue(number)

    def create_pr(self, title: str, body: str, branch: str, base: str | None = None) -> PullRequest:
        if base is None:
            base = self.get_default_branch()
        return self.repo.create_pull(
            title=title,
            body=body,
            head=branch,
            base=base,
        )

    def get_pr(self, number: int) -> PullRequest:
        return self.repo.get_pull(number)

    def get_pr_diff(self, pr_number: int) -> str:
        pr = self.get_pr(pr_number)
        files = pr.get_files()
        diff_parts = []
        for f in files:
            diff_parts.append(f"--- {f.filename}")
            diff_parts.append(f"+++ {f.filename}")
            if f.patch:
                diff_parts.append(f.patch)
        return "\n".join(diff_parts)

    def create_review(self, pr_number: int, body: str, approve: bool) -> None:
        pr = self.get_pr(pr_number)
        event = "APPROVE" if approve else "REQUEST_CHANGES"
        pr.create_review(body=body, event=event)

    def add_comment(self, pr_number: int, body: str) -> None:
        pr = self.get_pr(pr_number)
        pr.create_issue_comment(body)

    def get_ci_status(self, pr_number: int) -> CIStatus:
        pr = self.get_pr(pr_number)
        commit = pr.get_commits().reversed[0]
        check_runs = commit.get_check_runs()

        total = 0
        passed = 0
        failed_names = []

        for run in check_runs:
            total += 1
            if run.conclusion == "success":
                passed += 1
            elif run.conclusion in ("failure", "cancelled"):
                failed_names.append(run.name)

        if total == 0:
            return CIStatus(success=True, summary="Нет проверок")

        if failed_names:
            return CIStatus(
                success=False,
                summary=f"{passed}/{total} прошло, упали: {', '.join(failed_names)}"
            )

        return CIStatus(success=True, summary=f"{passed}/{total} прошло")

    def add_label(self, pr_number: int, label: str) -> None:
        pr = self.get_pr(pr_number)
        pr.add_to_labels(label)
