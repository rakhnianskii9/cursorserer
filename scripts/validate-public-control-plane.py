#!/usr/bin/env python3
"""Validate the public archive or a materialized local runtime.

This validator uses the Python standard library and, when available, PyYAML for
strict YAML parsing. It checks the release boundary rather than claiming that
optional Cursor or MCP capabilities are available in the current host.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST: dict = {}
CYRILLIC = re.compile(r"[\u0400-\u04ff]")
PRIVATE_PATTERNS = (
    re.compile(r"/home/[^$/{\s]+"),
    re.compile(r"/Users/[^$/{\s]+"),
    re.compile(r"(?i)\.cursor-server"),
    re.compile(r"(?i)\bZlogs\.md\b"),
    re.compile(r"(?i)\bUSER_HOME\b"),
    re.compile(r"(?i)\bConductor\b|\bConsilium\b|\bCopilot\b|\bClaude\b"),
    re.compile(r"(?i)\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?i)\b(?:xox[baprs]-|BEGIN [A-Z ]*PRIVATE KEY)"),
    re.compile(r"(?i)postgres(?:ql)?://[^$\s:/]+:[^$\s@]+@"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9/+._-]{16,}"),
    re.compile(r"(?i)@latest\b"),
)
LIFECYCLE_KINDS = {
    "started",
    "progress",
    "wave_result",
    "waiting_user",
    "blocked",
    "completed",
    "failed",
    "wave_cap",
}
BINARY_SUFFIXES = {
    ".apkg",
    ".gif",
    ".graffle",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".webp",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(f"FAIL {message}")


def configure_root(root: Path) -> None:
    global ROOT, MANIFEST
    ROOT = root.expanduser().resolve()
    MANIFEST = {}


def load_manifest(errors: list[str] | None = None) -> dict:
    global MANIFEST
    if MANIFEST:
        return MANIFEST
    path = ROOT / "PUBLIC-ARCHIVE-MANIFEST.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        if errors is not None:
            fail(errors, f"{path.relative_to(ROOT)} cannot be loaded: {error}")
        return {}
    if not isinstance(value, dict):
        if errors is not None:
            fail(errors, "PUBLIC-ARCHIVE-MANIFEST.json must contain an object")
        return {}
    MANIFEST = value
    return MANIFEST


def path_matches(value: str, patterns: Iterable[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(value, pattern)
        or PurePosixPath(value).match(pattern)
        for pattern in patterns
    )


def is_excluded_public_path(relative: Path) -> bool:
    manifest = load_manifest()
    return path_matches(
        relative.as_posix(), manifest.get("excluded_path_patterns", [])
    )


def git_paths() -> list[Path]:
    if not (ROOT / ".git").exists():
        return []
    result = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [Path(item) for item in result.stdout.decode().split("\0") if item]


def all_paths() -> list[Path]:
    paths = git_paths()
    if paths:
        return paths
    return [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    ]


def is_allowed_public_path(relative: Path) -> bool:
    value = relative.as_posix()
    if is_excluded_public_path(relative):
        return False
    manifest = load_manifest()
    if value.startswith("skills/"):
        parts = relative.parts
        if len(parts) < 3 or parts[1] not in manifest.get("public_skill_ids", []):
            return False
    return (
        value in manifest.get("release_files", [])
        or value in manifest.get("exact_public_files", [])
        or path_matches(value, manifest.get("public_file_patterns", []))
    )


def strip_jsonc(text: str) -> str:
    text = re.sub(r"(?m)^\s*//.*$", "", text)
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def validate_binary_files(paths: Iterable[Path], errors: list[str]) -> None:
    manifest = load_manifest(errors)
    reviews = {
        item.get("path"): item
        for item in manifest.get("binary_review", [])
        if isinstance(item, dict) and item.get("path")
    }
    allowed_patterns = manifest.get("binary_public_patterns", [])
    for relative in paths:
        if relative.suffix.lower() not in BINARY_SUFFIXES:
            continue
        value = relative.as_posix()
        if value not in reviews and not path_matches(value, allowed_patterns):
            fail(errors, f"{relative} is not in the binary public allowlist")
            continue
        path = ROOT / relative
        if path.is_symlink():
            fail(errors, f"{relative} is a symlink")
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            fail(errors, f"{relative} cannot be hashed: {error}")
            continue
        expected = reviews.get(value, {}).get("sha256")
        if expected and digest != expected:
            fail(errors, f"{relative} has an unexpected SHA-256: {digest}")
        if value in reviews and path.suffix.lower() == ".png":
            try:
                header = path.read_bytes()[:24]
                if header[:8] != b"\x89PNG\r\n\x1a\n":
                    raise ValueError("invalid PNG signature")
                width = int.from_bytes(header[16:20], "big")
                height = int.from_bytes(header[20:24], "big")
            except (OSError, ValueError) as error:
                fail(errors, f"{relative} has invalid PNG metadata: {error}")
                continue
            review = reviews[value]
            if review.get("width") != width or review.get("height") != height:
                fail(errors, f"{relative} dimensions do not match binary review metadata")


def validate_text_files(paths: Iterable[Path], errors: list[str]) -> None:
    for relative in paths:
        path = ROOT / relative
        if path.is_symlink():
            fail(errors, f"{relative} is a symlink")
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            text = read_text(path)
        except (OSError, UnicodeError) as error:
            fail(errors, f"{relative} cannot be read: {error}")
            continue
        if CYRILLIC.search(text):
            fail(errors, f"{relative} contains Cyrillic text")
        if relative.as_posix() != "scripts/validate-public-control-plane.py":
            for pattern in PRIVATE_PATTERNS:
                if pattern.search(text):
                    fail(
                        errors,
                        f"{relative} contains a private or mutable pattern: {pattern.pattern}",
                    )
        if "sample" in relative.name.lower() and not relative.as_posix().startswith(
            "reference/"
        ):
            fail(errors, f"{relative} still uses sample naming")


def validate_json(paths: Iterable[Path], errors: list[str]) -> None:
    for relative in paths:
        if relative.suffix != ".json":
            continue
        path = ROOT / relative
        try:
            json.loads(strip_jsonc(read_text(path)))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            fail(errors, f"{relative} is not valid JSON/JSONC: {error}")


def validate_python(paths: Iterable[Path], errors: list[str]) -> None:
    for relative in paths:
        if relative.suffix != ".py":
            continue
        try:
            ast.parse(read_text(ROOT / relative), filename=str(relative))
        except (OSError, UnicodeError, SyntaxError) as error:
            fail(errors, f"{relative} is not valid Python: {error}")


def validate_shell(paths: Iterable[Path], errors: list[str]) -> None:
    for relative in paths:
        if relative.suffix != ".sh":
            continue
        result = subprocess.run(
            ["bash", "-n", str(ROOT / relative)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode:
            fail(errors, f"{relative} failed bash -n: {result.stderr.strip()}")


def validate_yaml(paths: Iterable[Path], errors: list[str]) -> None:
    yaml_paths = [path for path in paths if path.suffix in {".yaml", ".yml"}]
    if not yaml_paths:
        return
    try:
        import yaml  # type: ignore
    except ImportError:
        for relative in yaml_paths:
            try:
                text = read_text(ROOT / relative)
            except (OSError, UnicodeError) as error:
                fail(errors, f"{relative} cannot be read: {error}")
                continue
            if "\t" in text:
                fail(errors, f"{relative} uses tabs, which are invalid YAML indentation")
        return
    for relative in yaml_paths:
        try:
            yaml.safe_load(read_text(ROOT / relative))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            fail(errors, f"{relative} is not valid YAML: {error}")


def validate_frontmatter(paths: Iterable[Path], errors: list[str]) -> None:
    for relative in paths:
        if not relative.name.endswith("SKILL.md"):
            continue
        try:
            text = read_text(ROOT / relative)
        except (OSError, UnicodeError) as error:
            fail(errors, f"{relative} cannot be read: {error}")
            continue
        if not text.startswith("---\n"):
            fail(errors, f"{relative} lacks YAML frontmatter")
            continue
        header = text.split("---\n", 2)
        if len(header) < 3:
            fail(errors, f"{relative} has malformed YAML frontmatter")
            continue
        if not re.search(r"(?m)^name:\s*\S+", header[1]):
            fail(errors, f"{relative} frontmatter lacks name")
        if not re.search(r"(?m)^description:\s*\S+", header[1]):
            fail(errors, f"{relative} frontmatter lacks description")


def validate_surface_links(paths: Iterable[Path], errors: list[str]) -> None:
    path_set = {path.as_posix() for path in paths}
    load_pattern = re.compile(r"Load `([^`]+)`")
    for relative in paths:
        if not relative.as_posix().startswith("commands/") or not relative.name.endswith(
            ".md"
        ):
            continue
        try:
            text = read_text(ROOT / relative)
        except (OSError, UnicodeError):
            continue
        for skill_name in load_pattern.findall(text):
            candidate = f"skills/{skill_name}/SKILL.md"
            if candidate not in path_set:
                fail(errors, f"{relative} loads missing public skill: {skill_name}")

    for relative in paths:
        if not relative.as_posix().startswith("agents/") or not relative.name.endswith(
            ".md"
        ):
            continue
        try:
            text = read_text(ROOT / relative)
        except (OSError, UnicodeError):
            continue
        if not text.startswith("---\n"):
            fail(errors, f"{relative} lacks agent frontmatter")
            continue
        header = text.split("---\n", 2)
        if len(header) < 3:
            fail(errors, f"{relative} has malformed agent frontmatter")
            continue
        if not re.search(r"(?m)^name:\s*\S+", header[1]):
            fail(errors, f"{relative} agent frontmatter lacks name")
        if not re.search(r"(?m)^description:\s*\S+", header[1]):
            fail(errors, f"{relative} agent frontmatter lacks description")
        model_match = re.search(r"(?m)^model:\s*(\S+)", header[1])
        if model_match and not model_match.group(1).startswith("__MODEL_"):
            fail(errors, f"{relative} claims an unverified model binding")


def is_declared_canonical_target(value: str, manifest: dict) -> bool:
    if not path_matches(value, manifest.get("canonical_target_patterns", [])):
        return False
    if value.startswith("skills/"):
        parts = PurePosixPath(value).parts
        return len(parts) >= 3 and parts[1] in manifest.get("public_skill_ids", [])
    return True


def validate_links(paths: Iterable[Path], errors: list[str]) -> None:
    link_pattern = re.compile(r"\]\((?!https?://|#)([^)]+)\)")
    manifest = load_manifest(errors)
    for relative in paths:
        if relative.suffix not in {".md", ".mdc"}:
            continue
        try:
            text = read_text(ROOT / relative)
        except (OSError, UnicodeError):
            continue
        for target in link_pattern.findall(text):
            target_path = target.split("#", 1)[0].strip("<>")
            if not target_path or target_path.startswith("${"):
                continue
            candidate = (ROOT / relative.parent / target_path).resolve()
            try:
                candidate_key = candidate.relative_to(ROOT).as_posix()
            except ValueError:
                candidate_key = ""
            is_canonical = bool(
                candidate_key
                and is_declared_canonical_target(candidate_key, manifest)
            )
            if candidate_key and is_excluded_public_path(Path(candidate_key)) and not is_canonical:
                fail(
                    errors,
                    f"{relative} links into an excluded or private path: {target_path}",
                )
                continue
            if not candidate.exists():
                if is_canonical:
                    # Canonical targets are created by the Chat installer, but
                    # only mappings declared by the manifest may be absent here.
                    continue
                else:
                    fail(errors, f"{relative} links to missing {target_path}")


def validate_declaration_imports(paths: Iterable[Path], errors: list[str]) -> None:
    import_pattern = re.compile(r'from\s+"(\.[^"]+)"')
    for relative in paths:
        if relative.suffix != ".ts" and not relative.name.endswith(".d.ts"):
            continue
        try:
            text = read_text(ROOT / relative)
        except (OSError, UnicodeError):
            continue
        for imported in import_pattern.findall(text):
            if not imported.endswith(".js"):
                continue
            target = (ROOT / relative.parent / imported[:-3]).with_suffix(".d.ts")
            if not target.exists():
                fail(errors, f"{relative} imports missing declaration {imported}")


def load_fixture(relative: str, errors: list[str]) -> dict:
    path = ROOT / relative
    try:
        value = json.loads(read_text(path))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail(errors, f"{relative} cannot be loaded: {error}")
        return {}
    if not isinstance(value, dict):
        fail(errors, f"{relative} must contain an object")
        return {}
    return value


def validate_contract_fixtures(errors: list[str]) -> None:
    wave = load_fixture("scripts/fixtures/control-plane/wave-spec-v1.json", errors)
    required_wave = {
        "schema_version",
        "kind",
        "run_id",
        "wave_id",
        "token_mode",
        "billing_credential_scope",
        "spec_revision",
        "confidence",
        "confidence_basis",
        "hypotheses",
        "slots",
        "dispatch",
        "stop_condition",
    }
    if required_wave - set(wave):
        fail(errors, "wave-spec fixture is missing a required field")
    if "decision_kind" in wave:
        fail(errors, "wave-spec fixture still uses decision_kind")
    if wave.get("dispatch", {}).get("mode") != "PARALLEL":
        fail(errors, "wave-spec fixture must use PARALLEL dispatch")
    if wave.get("dispatch", {}).get("join") != "MERGER":
        fail(errors, "wave-spec fixture must use a MERGER join")
    for hypothesis in wave.get("hypotheses", []):
        if not hypothesis.get("hypothesis_id") or not hypothesis.get("confidence_basis"):
            fail(errors, "wave-spec fixture hypothesis identity/basis is incomplete")

    terminal = load_fixture(
        "scripts/fixtures/control-plane/terminal-lifecycle.json", errors
    )
    required_terminal = {
        "schema_version",
        "conversation_id",
        "event_id",
        "run_id",
        "phase_id",
        "wave_id",
        "kind",
        "notification_type",
        "waiting_reason",
        "correlation_id",
        "problem_title",
        "summary",
    }
    if required_terminal - set(terminal):
        fail(errors, "terminal lifecycle fixture is incomplete")
    if terminal.get("kind") not in LIFECYCLE_KINDS:
        fail(errors, "terminal lifecycle fixture has an invalid kind")
    if terminal.get("full_verdict_available") is False and "full_verdict_url" in terminal:
        fail(errors, "terminal lifecycle fixture has a URL while unavailable")
    decision_artifact = terminal.get("decision_artifact") or {}
    digest = decision_artifact.get("sha256")
    if digest is not None and not re.fullmatch(r"[A-Fa-f0-9]{64}", str(digest)):
        fail(errors, "terminal lifecycle fixture has an invalid artifact digest")

    missing_wave = load_fixture(
        "scripts/fixtures/control-plane/lifecycle-missing-wave.json", errors
    )
    if "wave_id" in missing_wave or "wave" in missing_wave:
        fail(errors, "missing-wave fixture unexpectedly contains wave")
    invalid_kind = load_fixture(
        "scripts/fixtures/control-plane/lifecycle-invalid-kind.json", errors
    )
    if invalid_kind.get("kind") in LIFECYCLE_KINDS:
        fail(errors, "invalid-kind fixture unexpectedly uses a registered kind")
    invalid_url = load_fixture(
        "scripts/fixtures/control-plane/lifecycle-url-when-unavailable.json", errors
    )
    if not (
        invalid_url.get("full_verdict_available") is False
        and invalid_url.get("full_verdict_url")
    ):
        fail(errors, "invalid-url fixture does not exercise the unavailable URL boundary")

    valid_inputs = load_fixture(
        "scripts/fixtures/control-plane/runtime-inputs-valid.json", errors
    )
    if not (
        1 <= valid_inputs.get("pending_lease_seconds", 0) <= 3600
        and 1 <= valid_inputs.get("dedup_ttl_seconds", 0) <= 604800
        and 1 <= valid_inputs.get("notification_max_age_seconds", 0) <= 604800
    ):
        fail(errors, "runtime input fixture has an invalid TTL range")
    invalid_inputs = load_fixture(
        "scripts/fixtures/control-plane/runtime-inputs-invalid-ttl.json", errors
    )
    if invalid_inputs.get("notification_max_age_seconds", 1) != 0:
        fail(errors, "invalid TTL fixture no longer exercises a zero value")


def validate_json_schemas(errors: list[str]) -> None:
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError:
        return
    pairs = [
        ("schemas/wave-spec-v1.json", "scripts/fixtures/control-plane/wave-spec-v1.json"),
        (
            "schemas/lifecycle-artifact-v1.json",
            "scripts/fixtures/control-plane/terminal-lifecycle.json",
        ),
        (
            "schemas/runtime-inputs-v1.json",
            "scripts/fixtures/control-plane/runtime-inputs-valid.json",
        ),
    ]
    packet_dir = ROOT / "schemas" / "packets"
    packet_fixtures = ROOT / "scripts" / "fixtures" / "control-plane" / "packets"
    if packet_dir.is_dir() and packet_fixtures.is_dir():
        for schema_path in sorted(packet_dir.glob("*-v1.json")):
            fixture_path = packet_fixtures / schema_path.name
            if fixture_path.is_file():
                pairs.append(
                    (
                        schema_path.relative_to(ROOT).as_posix(),
                        fixture_path.relative_to(ROOT).as_posix(),
                    )
                )
    for schema_name, fixture_name in pairs:
        schema = load_fixture(schema_name, errors)
        fixture = load_fixture(fixture_name, errors)
        try:
            validator = Draft202012Validator(schema)
            validation_errors = sorted(
                validator.iter_errors(fixture), key=lambda error: list(error.path)
            )
        except SchemaError as error:
            fail(errors, f"{schema_name} cannot validate its fixture: {error}")
            continue
        for error in validation_errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            fail(errors, f"{fixture_name} violates {schema_name} at {location}: {error.message}")

        if schema_name == "schemas/wave-spec-v1.json":
            for forbidden_field in ("decision_kind", "status"):
                invalid = {**fixture, forbidden_field: "END"}
                if not list(validator.iter_errors(invalid)):
                    fail(
                        errors,
                        f"{schema_name} accepts the non-canonical {forbidden_field} field",
                    )


def validate_archive(
    paths: list[Path], errors: list[str], tmp_dir: Path | None = None
) -> None:
    load_manifest(errors)
    public = [path for path in paths if is_allowed_public_path(path)]
    unexpected = [path for path in paths if not is_allowed_public_path(path)]
    for path in unexpected:
        if path.parts and path.parts[0] not in {".git"}:
            fail(errors, f"non-public file is present in the archive surface: {path}")
    if not public:
        fail(errors, "no public files were discovered")
        return
    validate_text_files(public, errors)
    validate_binary_files(public, errors)
    validate_json(public, errors)
    validate_python(public, errors)
    validate_shell(public, errors)
    validate_yaml(public, errors)
    validate_frontmatter(public, errors)
    validate_surface_links(public, errors)
    validate_links(public, errors)
    validate_declaration_imports(public, errors)
    validate_contract_fixtures(errors)
    validate_json_schemas(errors)

    required = set(load_manifest().get("required_public_files", []))
    for path in sorted(required - {item.as_posix() for item in public}):
        fail(errors, f"required public file is missing: {path}")

    summary = ROOT / "hooks/rkx_write_easy_summary.py"
    if summary.is_file():
        result = subprocess.run(
            [sys.executable, "-B", str(summary)],
            cwd=ROOT,
            input="",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode:
            fail(errors, f"easy-summary smoke test failed: {result.stderr.strip()}")
    test_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "hooks"}
    if tmp_dir is not None:
        try:
            tmp_dir.mkdir(parents=True, exist_ok=True)
            if not os.access(tmp_dir, os.W_OK):
                raise OSError("directory is not writable")
            test_env["TMPDIR"] = str(tmp_dir)
        except OSError as error:
            fail(errors, f"hook test temporary directory is unavailable: {error}")
    test_result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "hooks", "-p", "test_*.py"],
        cwd=ROOT,
        env=test_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if test_result.returncode:
        fail(errors, f"public hook tests failed: {test_result.stderr.strip()}")


def validate_runtime(paths: list[Path], errors: list[str]) -> None:
    required = (
        ROOT / "hooks.json",
        ROOT / "hooks/rkx_write_easy_summary.py",
        ROOT / "hooks/rkx_lifecycle_common.py",
    )
    for path in required:
        if not path.is_file():
            fail(errors, f"runtime file is missing: {path.relative_to(ROOT)}")
        if path.is_symlink():
            fail(errors, f"runtime file must not be a symlink: {path.relative_to(ROOT)}")
    hooks = ROOT / "hooks.json"
    if hooks.is_file():
        try:
            data = json.loads(strip_jsonc(read_text(hooks)))
            commands = [
                item.get("command", "")
                for item in data.get("hooks", {}).get("stop", [])
                if isinstance(item, dict)
            ]
            if any("USER_HOME" in command or "__CONTROL_PLANE_ROOT__" in command for command in commands):
                fail(errors, "hooks.json contains an unresolved home/root placeholder")
            for command in commands:
                match = re.search(r"(?:bash|python3)\s+(.+)$", command)
                if match:
                    target = match.group(1).replace("${HOME}", str(Path.home()))
                    if not Path(target).is_file():
                        fail(errors, f"hook target does not exist: {target}")
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            fail(errors, f"hooks.json is invalid: {error}")
    summary = ROOT / "hooks/rkx_write_easy_summary.py"
    if summary.is_file():
        result = subprocess.run(
            [sys.executable, "-B", str(summary)],
            cwd=ROOT,
            input="",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode:
            fail(errors, f"easy-summary runtime smoke test failed: {result.stderr.strip()}")
    validate_python(
        [
            path.relative_to(ROOT)
            for path in (
                ROOT / "hooks/rkx_write_easy_summary.py",
                ROOT / "hooks/rkx_lifecycle_common.py",
            )
            if path.is_file()
        ],
        errors,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--archive", action="store_true")
    mode.add_argument("--runtime", action="store_true")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="archive or runtime root to validate",
    )
    parser.add_argument(
        "--tmp-dir",
        type=Path,
        help="writable temporary directory for hook tests",
    )
    args = parser.parse_args()
    configure_root(args.root)
    errors: list[str] = []
    paths = all_paths()
    if args.archive:
        validate_archive(paths, errors, args.tmp_dir)
    else:
        validate_runtime(paths, errors)
    if errors:
        print("\n".join(errors))
        print(f"FAIL public control-plane validation ({len(errors)} issue(s))")
        return 1
    print(f"PASS public control-plane validation ({'archive' if args.archive else 'runtime'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
