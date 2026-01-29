from pathlib import Path

IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".eggs", "*.egg-info",
}

# Файлы с описанием проекта читаем в первую очередь
PROJECT_FILES = ["README.md", "pyproject.toml", "package.json", "setup.py"]

MAX_FILE_SIZE = 10_000

MAX_CONTEXT_SIZE = 50_000


class ContextCollector:
    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path)

    def collect(self, issue_text: str) -> str:
        """Собрать контекст репозитория для LLM."""
        parts = []

        # 1. Структура директорий
        tree = self._build_tree()
        parts.append(f"## Структура проекта\n```\n{tree}\n```")

        # 2. Ключевые файлы проекта
        for filename in PROJECT_FILES:
            content = self._read_file(filename)
            if content:
                parts.append(f"## {filename}\n```\n{content}\n```")

        # 3. Файлы упомянутые в Issue
        keywords = self._extract_keywords(issue_text)
        relevant_files = self._find_relevant_files(keywords)
        for filepath in relevant_files:
            content = self._read_file(filepath)
            if content:
                parts.append(f"## {filepath}\n```\n{content}\n```")

        context = "\n\n".join(parts)
        if len(context) > MAX_CONTEXT_SIZE:
            context = context[:MAX_CONTEXT_SIZE] + "\n\n[...контекст обрезан...]"

        return context

    def _build_tree(self, max_depth: int = 3) -> str:
        """Построить дерево директорий."""
        lines = []
        self._walk_tree(self.repo_path, "", lines, 0, max_depth)
        return "\n".join(lines)

    def _walk_tree(self, path: Path, prefix: str, lines: list, depth: int, max_depth: int):
        if depth >= max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        except PermissionError:
            return

        entries = [e for e in entries if e.name not in IGNORE_DIRS]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                self._walk_tree(entry, prefix + extension, lines, depth + 1, max_depth)

    def _read_file(self, filepath: str | Path) -> str | None:
        """Прочитать файл если он существует и не слишком большой."""
        full_path = self.repo_path / filepath
        if not full_path.exists() or not full_path.is_file():
            return None

        try:
            content = full_path.read_text(encoding="utf-8")
            if len(content) > MAX_FILE_SIZE:
                content = content[:MAX_FILE_SIZE] + "\n\n[...файл обрезан...]"
            return content
        except (UnicodeDecodeError, PermissionError):
            return None

    def _extract_keywords(self, text: str) -> list[str]:
        """Извлечь потенциальные имена файлов/классов/функций из текста."""
        import re

        keywords = []

        # Ищем пути к файлам
        file_patterns = re.findall(r'[\w/]+\.(?:py|js|ts|json|yaml|yml|md)', text)
        keywords.extend(file_patterns)

        # Ищем имена в CamelCase
        camel_case = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text)
        keywords.extend(camel_case)

        # Ищем имена в snake_case
        snake_case = re.findall(r'\b[a-z]+_[a-z_]+\b', text)
        keywords.extend(snake_case)

        return list(set(keywords))

    def _find_relevant_files(self, keywords: list[str], max_files: int = 5) -> list[Path]:
        """Найти файлы которые могут быть релевантны по ключевым словам."""
        if not keywords:
            return []

        relevant = []
        for filepath in self.repo_path.rglob("*.py"):
            if any(ignored in filepath.parts for ignored in IGNORE_DIRS):
                continue

            filename = filepath.name
            rel_path = filepath.relative_to(self.repo_path)

            for keyword in keywords:
                if keyword.lower() in filename.lower() or keyword.lower() in str(rel_path).lower():
                    relevant.append(rel_path)
                    break

            if len(relevant) >= max_files:
                break

        return relevant
