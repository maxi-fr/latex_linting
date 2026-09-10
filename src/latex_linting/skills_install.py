import importlib.resources
import shutil
from collections.abc import Mapping
from pathlib import Path


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
            installed.append(target)
    return installed
