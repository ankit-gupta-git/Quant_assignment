"""
app/agents/commit_writer.py
────────────────────────────
AI SDLC Agent: Conventional Commit Message Generator

Reads ``git diff --staged`` output and produces a Conventional Commits
(https://www.conventionalcommits.org) message automatically.

Usage (CLI):
    python -m app.agents.commit_writer

Or pipe diff directly:
    git diff --staged | python -m app.agents.commit_writer --stdin

The agent uses heuristic rules (no LLM dependency) so it works offline
in CI without API keys.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ── Commit type inference ─────────────────────────────────────────────────────

_PATH_TO_TYPE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^tests/"), "test"),
    (re.compile(r"docs/|README|\.md$"), "docs"),
    (re.compile(r"pyproject\.toml|requirements"), "build"),
    (re.compile(r"\.github/|Makefile|Dockerfile"), "ci"),
    (re.compile(r"app/domain/"), "feat"),
    (re.compile(r"app/strategy/"), "feat"),
    (re.compile(r"app/risk/"), "feat"),
    (re.compile(r"app/indicators/"), "feat"),
    (re.compile(r"app/backtest/"), "feat"),
    (re.compile(r"app/broker/"), "feat"),
    (re.compile(r"app/execution/"), "feat"),
    (re.compile(r"app/storage/"), "feat"),
    (re.compile(r"app/monitoring/"), "feat"),
    (re.compile(r"app/macro/"), "feat"),
    (re.compile(r"app/agents/"), "chore"),
    (re.compile(r"app/core/"), "refactor"),
]

_BREAKING_KEYWORDS = re.compile(
    r"\b(breaking|BREAKING|removes?|deletes?|renames?)\b", re.IGNORECASE
)


@dataclass
class DiffSummary:
    """Parsed summary of a git diff."""

    added_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]
    lines_added: int
    lines_removed: int


def parse_diff(diff_text: str) -> DiffSummary:
    """
    Parse raw ``git diff`` output into a structured summary.

    Args:
        diff_text: Raw diff string (output of ``git diff --staged``).

    Returns:
        Populated DiffSummary.
    """
    added: list[str] = []
    modified: list[str] = []
    deleted: list[str] = []
    lines_added = 0
    lines_removed = 0

    current_file: Optional[str] = None
    is_new = False
    is_deleted = False

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            # Commit previous file
            if current_file:
                if is_new:
                    added.append(current_file)
                elif is_deleted:
                    deleted.append(current_file)
                else:
                    modified.append(current_file)
            # Reset
            match = re.search(r"b/(.+)$", line)
            current_file = match.group(1) if match else None
            is_new = False
            is_deleted = False
        elif line.startswith("new file mode"):
            is_new = True
        elif line.startswith("deleted file mode"):
            is_deleted = True
        elif line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    # Commit last file
    if current_file:
        if is_new:
            added.append(current_file)
        elif is_deleted:
            deleted.append(current_file)
        else:
            modified.append(current_file)

    return DiffSummary(
        added_files=added,
        modified_files=modified,
        deleted_files=deleted,
        lines_added=lines_added,
        lines_removed=lines_removed,
    )


def infer_commit_type(summary: DiffSummary) -> str:
    """
    Infer the Conventional Commit type from file paths.

    Priority: deleted → fix, all paths matched → highest priority type.

    Args:
        summary: Parsed diff summary.

    Returns:
        Commit type string (feat, fix, docs, test, refactor, chore, build, ci).
    """
    if summary.deleted_files:
        return "fix"

    all_files = summary.added_files + summary.modified_files
    if not all_files:
        return "chore"

    type_counts: dict[str, int] = {}
    for path in all_files:
        for pattern, ctype in _PATH_TO_TYPE:
            if pattern.search(path):
                type_counts[ctype] = type_counts.get(ctype, 0) + 1
                break
        else:
            type_counts["chore"] = type_counts.get("chore", 0) + 1

    return max(type_counts, key=lambda k: type_counts[k])


def infer_scope(summary: DiffSummary) -> str:
    """
    Infer the scope from the most changed directory.

    Args:
        summary: Parsed diff summary.

    Returns:
        Short scope string (e.g. ``strategy``, ``risk``, ``backtest``).
    """
    all_files = summary.added_files + summary.modified_files + summary.deleted_files
    dir_counts: dict[str, int] = {}
    for path in all_files:
        parts = Path(path).parts
        if len(parts) >= 2 and parts[0] == "app":
            scope = parts[1]
        elif parts:
            scope = parts[0]
        else:
            scope = "core"
        dir_counts[scope] = dir_counts.get(scope, 0) + 1

    if not dir_counts:
        return "core"
    return max(dir_counts, key=lambda k: dir_counts[k])


def build_description(summary: DiffSummary) -> str:
    """
    Build a short commit description from the diff summary.

    Args:
        summary: Parsed diff summary.

    Returns:
        One-line imperative-mood description.
    """
    parts: list[str] = []

    if summary.added_files:
        n = len(summary.added_files)
        names = ", ".join(Path(f).stem for f in summary.added_files[:3])
        suffix = f" and {n - 3} more" if n > 3 else ""
        parts.append(f"add {names}{suffix}")

    if summary.modified_files:
        n = len(summary.modified_files)
        names = ", ".join(Path(f).stem for f in summary.modified_files[:3])
        suffix = f" and {n - 3} more" if n > 3 else ""
        parts.append(f"update {names}{suffix}")

    if summary.deleted_files:
        n = len(summary.deleted_files)
        names = ", ".join(Path(f).stem for f in summary.deleted_files[:2])
        suffix = f" and {n - 2} more" if n > 2 else ""
        parts.append(f"remove {names}{suffix}")

    if not parts:
        return "apply changes"

    return "; ".join(parts)


def generate_commit_message(diff_text: str) -> str:
    """
    Generate a full Conventional Commit message from a git diff string.

    Args:
        diff_text: Raw output of ``git diff --staged``.

    Returns:
        Formatted commit message string.
    """
    summary = parse_diff(diff_text)
    ctype = infer_commit_type(summary)
    scope = infer_scope(summary)
    description = build_description(summary)

    is_breaking = bool(_BREAKING_KEYWORDS.search(diff_text))
    breaking_suffix = "!" if is_breaking else ""

    header = f"{ctype}({scope}){breaking_suffix}: {description}"

    body_lines = [
        f"Changed files: {len(summary.added_files + summary.modified_files + summary.deleted_files)}",
        f"Lines added: +{summary.lines_added}",
        f"Lines removed: -{summary.lines_removed}",
    ]
    if is_breaking:
        body_lines.append("\nBREAKING CHANGE: review API compatibility before merging.")

    body = "\n".join(body_lines)
    return f"{header}\n\n{body}"


def get_staged_diff() -> str:
    """Run ``git diff --staged`` and return the output."""
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a Conventional Commit message from git diff"
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read diff from stdin instead of running git diff --staged",
    )
    args = parser.parse_args(argv)

    if args.stdin:
        diff_text = sys.stdin.read()
    else:
        diff_text = get_staged_diff()

    if not diff_text.strip():
        print("No staged changes found. Stage files with 'git add' first.")
        sys.exit(0)

    message = generate_commit_message(diff_text)
    print("\n── Generated Commit Message ───────────────────────────────")
    print(message)
    print("──────────────────────────────────────────────────────────")
    print("\nCopy with:  git commit -m '<message>'")


if __name__ == "__main__":
    main()
