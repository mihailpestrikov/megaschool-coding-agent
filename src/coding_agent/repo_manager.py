import shutil
import tempfile
from pathlib import Path

from git import Repo


class RepoManager:
    def clone(self, repo_url: str, token: str) -> Path:
        tmpdir = tempfile.mkdtemp(prefix="agent-")
        auth_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
        Repo.clone_from(auth_url, tmpdir, depth=1)
        return Path(tmpdir)

    def cleanup(self, path: Path):
        if path.exists():
            shutil.rmtree(path)
