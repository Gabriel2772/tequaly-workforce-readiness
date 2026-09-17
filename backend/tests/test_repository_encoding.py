import os
from pathlib import Path


def test_repository_text_has_no_replacement_characters() -> None:
    project_root = Path(__file__).parents[2]
    ignored_directories = {
        ".git",
        ".next",
        ".runtime",
        ".venv",
        "__pycache__",
        "logs",
        "node_modules",
    }
    offenders: list[str] = []

    for directory, subdirectories, filenames in os.walk(project_root):
        subdirectories[:] = [
            name for name in subdirectories if name not in ignored_directories
        ]
        for filename in filenames:
            path = Path(directory) / filename
            if b"\xef\xbf\xbd" in path.read_bytes():
                offenders.append(str(path.relative_to(project_root)))

    assert offenders == []
