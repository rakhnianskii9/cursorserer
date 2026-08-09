#!/usr/bin/env python3
"""Build a deterministic public archive from the manifest inventory."""

from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import sys
from pathlib import Path, PurePosixPath


MANIFEST_NAME = "PUBLIC-ARCHIVE-MANIFEST.json"
TEMPLATE_NAME = ".gitignore.example"

FALLBACK_GITIGNORE = """\
# Generated public archive ignore policy.
*
!.gitignore
!README.md
!INSTALL-WITH-CURSOR.md
!LICENSE
!NOTICE
!PUBLIC-ARCHIVE-MANIFEST.json
!CANONICAL-PROTOCOLS.md
!MCP-CAPABILITY-MATRIX.example.md
!mcp.json.example
!settings.example.json
!hooks.example.json
!CURSOR-UX.example.md
!CURSOR-MODELS.example.md
!RKX-LOOP-BLUEPRINT-FLOW.example.md
!agents/
!agents/*.example.md
!commands/
!commands/*.example.md
!hooks/
!hooks/*.example.py
!hooks/*_example.py
!hooks/*.example.sh
!hooks/*.env.example
!rules/
!rules/*.example.mdc
!scripts/
!scripts/**
!schemas/
!schemas/**
!reference/
!reference/**
!skills/
!skills/**/
!skills/**/SKILL.example.md
!skills/**/project-map.example.md
!skills/**/recipes.example.md
!skills/**/project-tenets.example.md
!skills/refero-design/references/
!skills/refero-design/references/**
!loops/
!loops/README.md
!loops/_decisions/
!loops/_decisions/**
!loops/*.example.md
!vendor/
!vendor/**
!runtime/
!runtime/logs/
!runtime/logs/README.md
!assets/
!assets/rkx-loop-flow.png
!assets/install-flow.png
/reference/blueprint-index.yaml
/reference/system-design-primer/README-ja.md
/reference/system-design-primer/README-zh-*.md
/reference/system-design-primer/**/README-zh-*.md
/reference/system-design-primer/TRANSLATIONS.md
/reference/system-design-primer/.github/
/reference/system-design-primer/.gitignore
/reference/system-design-primer/generate-epub.sh
/reference/system-design-primer/resources/
/prompts/
/projects/
/plans/
/plugins/
/subagents/
/sandbox-policies/
/skills-cursor/
/runtime/logs/*
!/runtime/logs/README.md
/loops/*/manifest.md
/loops/*/slack-notification.json
/loops/*/state.md
/loops/*/wave-*/
"""


def relative_key(path: Path) -> str:
    return PurePosixPath(path.as_posix()).as_posix()


def matches(path: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, pattern)
        or PurePosixPath(path).match(pattern)
        for pattern in patterns
    )


def load_manifest(source_root: Path) -> dict:
    manifest_path = source_root / MANIFEST_NAME
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot load {manifest_path}: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit(f"{manifest_path} must contain a JSON object")
    return value


def excluded(path: str, manifest: dict) -> bool:
    return matches(path, manifest.get("excluded_path_patterns", []))


def public_path(path: str, manifest: dict) -> bool:
    if excluded(path, manifest):
        return False
    if path.startswith("skills/"):
        parts = PurePosixPath(path).parts
        if len(parts) < 3 or parts[1] not in manifest.get("public_skill_ids", []):
            return False
    if path in manifest.get("release_files", []):
        return True
    if path in manifest.get("exact_public_files", []):
        return True
    return matches(path, manifest.get("public_file_patterns", []))


def write_public_gitignore(source_root: Path, output_root: Path) -> None:
    template = source_root / TEMPLATE_NAME
    contents = (
        template.read_text(encoding="utf-8")
        if template.is_file()
        else FALLBACK_GITIGNORE
    )
    target = output_root / ".gitignore"
    target.write_text(contents, encoding="utf-8")


def copy_public_files(source_root: Path, output_root: Path, manifest: dict) -> int:
    copied = 0
    root_names = {
        pattern.split("/", 1)[0]
        for pattern in manifest.get("public_file_patterns", [])
        if "/" in pattern
    }
    root_names.update(
        Path(path).parts[0]
        for path in manifest.get("exact_public_files", [])
        if Path(path).parts
    )
    root_names.update(
        Path(path).parts[0]
        for path in manifest.get("release_files", [])
        if "/" in path and path != ".gitignore"
    )
    candidates: list[Path] = []
    for root_name in sorted(root_names):
        root = source_root / root_name
        if root.is_dir():
            candidates.extend(root.rglob("*"))
    for path in manifest.get("release_files", []):
        if "/" not in path and path != ".gitignore":
            candidate = source_root / path
            if candidate.exists():
                candidates.append(candidate)
    candidates = sorted(set(candidates))
    for source in candidates:
        relative = source.relative_to(source_root)
        key = relative_key(relative)
        if key == ".gitignore" or not public_path(key, manifest):
            continue
        if source.is_symlink():
            raise SystemExit(f"Public archive cannot contain a symlink: {key}")
        if not source.is_file():
            continue
        target = output_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="new output directory; it must not already exist",
    )
    args = parser.parse_args()

    source_root = Path(__file__).resolve().parents[1]
    output_root = args.out.expanduser().resolve()
    if output_root.exists():
        raise SystemExit(f"Output directory already exists: {output_root}")
    if output_root == source_root or source_root in output_root.parents:
        raise SystemExit("Output directory must not be inside the source workspace")

    manifest = load_manifest(source_root)
    output_root.mkdir(parents=True)
    copied = copy_public_files(source_root, output_root, manifest)
    write_public_gitignore(source_root, output_root)

    print(f"Staged {copied + 1} public files at {output_root}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
