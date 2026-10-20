import importlib.resources
import re
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

_MAX_SHORT_DESC_LEN = 90
_FRONTMATTER_SPLIT_PARTS = 3


def _derive_display_name(name: str) -> str:
    """Derive human-facing title from skill name."""
    acronyms = {"tdd": "TDD", "ts": "TS", "api": "API", "ui": "UI", "cli": "CLI", "latex": "LaTeX", "pdf": "PDF"}
    words = [w for w in re.split(r"[-_]+", name.strip()) if w]
    return " ".join(acronyms.get(w.lower(), w.capitalize()) for w in words)


def _derive_short_description(description: str) -> str:
    """Derive concise description from frontmatter description."""
    clean = " ".join(description.strip().split())
    if len(clean) <= _MAX_SHORT_DESC_LEN:
        return clean
    match = re.match(r"^([^.?!]+[.?!])", clean)
    if match and len(match.group(1)) <= _MAX_SHORT_DESC_LEN:
        return match.group(1).strip()
    comma_part = clean.split(",", 1)[0].strip()
    if len(comma_part) <= _MAX_SHORT_DESC_LEN:
        return comma_part
    return clean[: _MAX_SHORT_DESC_LEN - 3] + "..."


def _extract_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter mapping from markdown content."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < _FRONTMATTER_SPLIT_PARTS:
        return {}
    data = yaml.safe_load(parts[1])
    return data if isinstance(data, dict) else {}


def generate_openai_yaml(skill_dir: Path) -> Path | None:
    """Generate agents/openai.yaml inside skill directory from SKILL.md frontmatter."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return None
    frontmatter = _extract_frontmatter(skill_file.read_text(encoding="utf-8"))
    if not frontmatter:
        return None

    overrides = frontmatter.get("openai")
    openai_overrides: dict[str, Any] = overrides if isinstance(overrides, dict) else {}
    display_name = openai_overrides.get("display_name") or _derive_display_name(
        str(frontmatter.get("name", skill_dir.name))
    )
    raw_desc = str(frontmatter.get("description", ""))
    short_desc = openai_overrides.get("short_description") or _derive_short_description(raw_desc)

    lines = [
        "interface:",
        f'  display_name: "{display_name}"',
        f'  short_description: "{short_desc}"',
    ]
    if frontmatter.get("disable-model-invocation") is True:
        lines.extend(
            [
                "policy:",
                "  allow_implicit_invocation: false",
            ]
        )

    target_dir = skill_dir / "agents"
    target_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = target_dir / "openai.yaml"
    yaml_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return yaml_file


def get_preset_destinations() -> Mapping[str, Path]:
    """Return mapping of preset names to destination directories."""
    return {
        "local": Path.cwd() / ".agents" / "skills",
        "global": Path.home() / ".agents" / "skills",
        "claude": Path.cwd() / ".claude" / "skills",
        "claude-global": Path.home() / ".claude" / "skills",
    }


def resolve_install_destination(
    preset: str | None,
    dest: Path | None,
    presets: Mapping[str, Path] | None = None,
) -> Path:
    """Resolve destination directory from preset name and custom destination options."""
    if preset is not None and dest is not None:
        msg = "cannot specify both preset and --dest"
        raise ValueError(msg)
    available = presets if presets is not None else get_preset_destinations()
    if dest is not None:
        return dest
    if preset is not None:
        if preset not in available:
            msg = f"unknown preset: {preset}"
            raise ValueError(msg)
        return available[preset]
    return available["local"]


def install_skills(destination: Path, *, force: bool = False) -> list[Path]:
    """Install bundled skills into destination directory, returning paths to installed skill folders."""
    skills_root = importlib.resources.files("latex_linting.skills")
    installed: list[Path] = []
    with importlib.resources.as_file(skills_root) as root_path:
        skill_dirs = sorted(
            [item for item in root_path.iterdir() if item.is_dir() and not item.name.startswith(("_", "."))],
            key=lambda p: p.name,
        )
        for skill_dir in skill_dirs:
            target = destination / skill_dir.name
            if target.exists() and not force:
                msg = f"skill '{skill_dir.name}' already exists at '{target}'. Use --force to overwrite."
                raise FileExistsError(msg)
        destination.mkdir(parents=True, exist_ok=True)
        for skill_dir in skill_dirs:
            target = destination / skill_dir.name
            shutil.copytree(skill_dir, target, dirs_exist_ok=True)
            if not (target / "agents" / "openai.yaml").exists():
                generate_openai_yaml(target)
            installed.append(target)
    return installed
