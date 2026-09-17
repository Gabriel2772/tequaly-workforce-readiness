from pathlib import Path


def test_user_facing_source_has_no_utf8_mojibake() -> None:
    project_root = Path(__file__).parents[2]
    roots = (
        project_root / "backend" / "app",
        project_root / "frontend" / "app",
        project_root / "frontend" / "components",
        project_root / "frontend" / "features",
        project_root / "frontend" / "lib",
        project_root / "frontend" / "e2e",
    )
    mojibake = (
        "Ã­",
        "Ã¡",
        "Â·",
        "Ã§",
        "Ã©",
        "Ã¢",
        "Ã£",
        "â€¦",
        "Ã³",
        "Ãª",
        "Ãµ",
    )
    offenders: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.suffix not in {".py", ".ts", ".tsx"}:
                continue
            content = path.read_text(encoding="utf-8")
            if any(marker in content for marker in mojibake):
                offenders.append(str(path.relative_to(project_root)))

    assert offenders == []
