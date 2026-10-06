from __future__ import annotations

import csv
import io
import json
import shutil
import subprocess
from pathlib import Path


KAGGLE_USER = "wasjaip"
ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = ROOT / "kaggle"
INDEX_FILE = ROOT / "KAGGLE_INDEX.md"
PAGE_SIZE = 100


def run_command(args: list[str]) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def extract_ref(row: dict[str, str]) -> str | None:
    # В разных версиях Kaggle CLI имя поля с идентификатором может отличаться.
    for key in ("ref", "id", "kernelRef", "kernel_ref"):
        value = row.get(key)
        if value and "/" in value:
            return value.strip()

    for value in row.values():
        if value and "/" in value and " " not in value:
            return value.strip()

    return None


def list_kernels() -> list[str]:
    refs: list[str] = []
    page = 1

    while True:
        output = run_command(
            [
                "kaggle",
                "kernels",
                "list",
                "--user",
                KAGGLE_USER,
                "--kernel-type",
                "notebook",
                "--page-size",
                str(PAGE_SIZE),
                "-p",
                str(page),
                "-v",
                "--sort-by",
                "dateRun",
            ]
        )

        rows = list(csv.DictReader(io.StringIO(output)))
        if not rows:
            break

        page_refs = [ref for row in rows if (ref := extract_ref(row))]
        refs.extend(page_refs)

        if len(rows) < PAGE_SIZE:
            break

        page += 1

    # Сохраняем порядок, но удаляем возможные дубли.
    return list(dict.fromkeys(refs))


def strip_notebook_outputs(path: Path) -> None:
    # В Git храним код и markdown, а тяжёлые результаты выполнения остаются на Kaggle.
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return

    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    path.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )


def notebook_headings(path: Path, limit: int = 8) -> list[str]:
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []

    headings: list[str] = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue

        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else str(source)

        for line in text.splitlines():
            value = line.strip()
            if value.startswith("#"):
                heading = value.lstrip("#").strip()
                if heading and heading not in headings:
                    headings.append(heading)
            if len(headings) >= limit:
                return headings

    return headings


def metadata_list(metadata: dict, key: str) -> list[str]:
    value = metadata.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def write_project_readme(project_dir: Path, kernel_ref: str) -> dict[str, str]:
    metadata_path = project_dir / "kernel-metadata.json"
    metadata = {}

    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    title = str(metadata.get("title") or kernel_ref.split("/", 1)[-1])
    code_file = str(metadata.get("code_file") or "")
    notebook_path = project_dir / code_file if code_file else None

    if notebook_path and notebook_path.exists() and notebook_path.suffix == ".ipynb":
        strip_notebook_outputs(notebook_path)
        headings = notebook_headings(notebook_path)
    else:
        headings = []

    competition_sources = metadata_list(metadata, "competition_sources")
    dataset_sources = metadata_list(metadata, "dataset_sources")
    kernel_sources = metadata_list(metadata, "kernel_sources")

    lines = [
        f"# {title}",
        "",
        f"Оригинал на Kaggle: https://www.kaggle.com/code/{kernel_ref}",
        "",
        "## Метаданные",
        "",
        f"- Автор: `{KAGGLE_USER}`",
        f"- Тип: `{metadata.get('kernel_type', 'notebook')}`",
        f"- Язык: `{metadata.get('language', 'python')}`",
    ]

    if code_file:
        lines.append(f"- Код: [`{code_file}`]({code_file})")

    if competition_sources:
        lines.extend(["", "## Соревнования", ""])
        lines.extend(
            f"- [{item}](https://www.kaggle.com/competitions/{item})"
            for item in competition_sources
        )

    if dataset_sources:
        lines.extend(["", "## Датасеты", ""])
        lines.extend(
            f"- [{item}](https://www.kaggle.com/datasets/{item})"
            for item in dataset_sources
        )

    if kernel_sources:
        lines.extend(["", "## Использованные Kaggle notebooks", ""])
        lines.extend(
            f"- [{item}](https://www.kaggle.com/code/{item})"
            for item in kernel_sources
        )

    if headings:
        lines.extend(["", "## Разделы ноутбука", ""])
        lines.extend(f"- {heading}" for heading in headings)

    lines.extend(
        [
            "",
            "## Примечание",
            "",
            "Репозиторий хранит исходный код решения. Результаты выполнения и актуальная версия доступны по ссылке на Kaggle.",
            "",
        ]
    )

    (project_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")

    return {
        "title": title,
        "ref": kernel_ref,
        "slug": kernel_ref.split("/", 1)[-1],
        "competitions": ", ".join(competition_sources),
    }


def sync_kernel(kernel_ref: str) -> dict[str, str] | None:
    slug = kernel_ref.split("/", 1)[-1]
    project_dir = SYNC_DIR / slug

    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    run_command(
        [
            "kaggle",
            "kernels",
            "pull",
            kernel_ref,
            "-p",
            str(project_dir),
            "-m",
        ]
    )

    metadata_path = project_dir / "kernel-metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if str(metadata.get("is_private", "false")).lower() == "true":
            shutil.rmtree(project_dir)
            return None

    return write_project_readme(project_dir, kernel_ref)


def write_index(projects: list[dict[str, str]]) -> None:
    lines = [
        "# Kaggle portfolio",
        "",
        f"Автоматически синхронизированные публичные notebooks пользователя [{KAGGLE_USER}](https://www.kaggle.com/{KAGGLE_USER}).",
        "",
        "| Решение | Соревнование | Kaggle | GitHub |",
        "| --- | --- | --- | --- |",
    ]

    for project in projects:
        title = project["title"].replace("|", "\\|")
        competitions = project["competitions"].replace("|", "\\|") or "—"
        lines.append(
            f"| {title} | {competitions} | [открыть](https://www.kaggle.com/code/{project['ref']}) | "
            f"[код](kaggle/{project['slug']}/) |"
        )

    lines.extend(
        [
            "",
            "## Как обновляется каталог",
            "",
            "Каталог формируется скриптом `scripts/sync_kaggle.py` через официальный Kaggle CLI.",
            "",
        ]
    )

    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    SYNC_DIR.mkdir(parents=True, exist_ok=True)
    refs = list_kernels()

    projects: list[dict[str, str]] = []
    for kernel_ref in refs:
        print(f"Синхронизация: {kernel_ref}")
        project = sync_kernel(kernel_ref)
        if project:
            projects.append(project)

    write_index(projects)
    print(f"Готово. Синхронизировано notebooks: {len(projects)}")


if __name__ == "__main__":
    main()
