import subprocess
from pathlib import Path


MAX_TRACKED_FILE_LINES = 1000


def test_tracked_files_stay_under_1000_lines():
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    violations = []

    for relative_path in result.stdout.splitlines():
        path = repo_root / relative_path

        if not path.is_file():
            continue

        contents = path.read_bytes()
        line_count = contents.count(b"\n")

        if contents and not contents.endswith(b"\n"):
            line_count += 1

        if line_count > MAX_TRACKED_FILE_LINES:
            violations.append(f"{relative_path}: {line_count} lines")

    assert violations == []
