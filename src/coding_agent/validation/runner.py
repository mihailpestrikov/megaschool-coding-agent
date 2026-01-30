import subprocess
from dataclasses import dataclass

ALLOWED_COMMANDS = {
    "ruff", "pytest", "python", "pip", "mypy", "black", "flake8", "pylint",
    "npm", "npx", "yarn", "pnpm", "node", "tsc",
    "go", "cargo", "rustc",
    "mvn", "gradle", "javac",
    "make", "sh", "bash",
}

TIMEOUT_SECONDS = 60


@dataclass
class ValidationResult:
    success: bool
    output: str
    command: str


def is_command_allowed(command: str) -> bool:
    first_word = command.strip().split()[0] if command.strip() else ""
    return first_word in ALLOWED_COMMANDS


def run_validation(commands: list[str], cwd: str = ".") -> list[ValidationResult]:
    results = []

    for cmd in commands:
        if not is_command_allowed(cmd):
            results.append(ValidationResult(False, f"Команда не разрешена: {cmd}", cmd))
            continue

        try:
            proc = subprocess.run(
                cmd, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
            )
            results.append(ValidationResult(proc.returncode == 0, proc.stdout + proc.stderr, cmd))
        except subprocess.TimeoutExpired:
            results.append(ValidationResult(False, f"Таймаут ({TIMEOUT_SECONDS}s)", cmd))
        except Exception as e:
            results.append(ValidationResult(False, str(e), cmd))

    return results
