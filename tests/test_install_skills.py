import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

from latex_linting.cli import main
from latex_linting.skills_install import (
    get_preset_destinations,
    install_skills,
    resolve_install_destination,
)


def test_resolve_destination_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    dest = resolve_install_destination(None, None)
    assert dest == tmp_path / ".agents" / "skills"


def test_resolve_destination_presets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    presets = get_preset_destinations()
    assert presets["local"] == tmp_path / ".agents" / "skills"
    assert presets["global"] == fake_home / ".agents" / "skills"
    assert presets["claude"] == tmp_path / ".claude" / "skills"
    assert presets["claude-global"] == fake_home / ".claude" / "skills"

    assert resolve_install_destination("local", None) == tmp_path / ".agents" / "skills"
    assert resolve_install_destination("global", None) == fake_home / ".agents" / "skills"
    assert resolve_install_destination("claude", None) == tmp_path / ".claude" / "skills"
    assert resolve_install_destination("claude-global", None) == fake_home / ".claude" / "skills"


def test_resolve_destination_custom_dest(tmp_path: Path) -> None:
    custom = tmp_path / "custom" / "skills"
    assert resolve_install_destination(None, custom) == custom


def test_resolve_destination_conflicting_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot specify both"):
        resolve_install_destination("local", tmp_path)


def test_install_skills_copies_files(tmp_path: Path) -> None:
    dest = tmp_path / "skills"
    installed = install_skills(dest)
    installed_names = {p.name for p in installed}
    assert installed_names == {"thesis-writing", "thesis-review", "citation-checker"}
    for skill_name in ["thesis-writing", "thesis-review", "citation-checker"]:
        skill_file = dest / skill_name / "SKILL.md"
        assert skill_file.is_file()
        content = skill_file.read_text(encoding="utf-8")
        assert f"name: {skill_name}" in content or "name: thesis-" in content


def test_install_skills_fails_if_exists_without_force(tmp_path: Path) -> None:
    dest = tmp_path / "skills"
    target_writing = dest / "thesis-writing"
    target_writing.mkdir(parents=True)
    dummy_file = target_writing / "dummy.txt"
    dummy_file.write_text("dummy", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        install_skills(dest, force=False)

    assert dummy_file.exists()


def test_install_skills_force_overwrites(tmp_path: Path) -> None:
    dest = tmp_path / "skills"
    target_writing = dest / "thesis-writing"
    target_writing.mkdir(parents=True)
    old_file = target_writing / "SKILL.md"
    old_file.write_text("old content", encoding="utf-8")

    installed = install_skills(dest, force=True)
    assert len(installed) == 3
    assert "old content" not in old_file.read_text(encoding="utf-8")


def test_cli_install_skills_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = StringIO()
    monkeypatch.setattr(sys, "stdout", out)

    exit_code = main(["install-skills"])
    assert exit_code == 0
    assert (tmp_path / ".agents" / "skills" / "thesis-writing" / "SKILL.md").is_file()
    assert (tmp_path / ".agents" / "skills" / "thesis-review" / "SKILL.md").is_file()
    assert (tmp_path / ".agents" / "skills" / "citation-checker" / "SKILL.md").is_file()
    assert "Installed thesis-writing" in out.getvalue()
    assert "Installed thesis-review" in out.getvalue()
    assert "Installed citation-checker" in out.getvalue()


def test_cli_install_skills_preset_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    exit_code = main(["install-skills", "claude"])
    assert exit_code == 0
    assert (tmp_path / ".claude" / "skills" / "thesis-writing" / "SKILL.md").is_file()


def test_cli_install_skills_custom_dest(tmp_path: Path) -> None:
    target = tmp_path / "custom_location"
    exit_code = main(["install-skills", "--dest", str(target)])
    assert exit_code == 0
    assert (target / "thesis-writing" / "SKILL.md").is_file()


def test_cli_install_skills_conflict_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    exit_code = main(["install-skills", "local", "--dest", str(tmp_path)])
    assert exit_code == 2
    assert "cannot specify both" in err.getvalue()


def test_cli_install_skills_already_exists_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "skills"
    (target / "thesis-writing").mkdir(parents=True)
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)

    exit_code = main(["install-skills", "--dest", str(target)])
    assert exit_code == 2
    assert "already exists" in err.getvalue()
    assert "--force" in err.getvalue()


def test_cli_install_skills_force_flag(tmp_path: Path) -> None:
    target = tmp_path / "skills"
    (target / "thesis-writing").mkdir(parents=True)
    exit_code = main(["install-skills", "--dest", str(target), "--force"])
    assert exit_code == 0
    assert (target / "thesis-writing" / "SKILL.md").is_file()


def test_subprocess_cli_install_skills(tmp_path: Path) -> None:
    executable = shutil.which("latex-lint")
    assert executable is not None
    target = tmp_path / "installed_skills"
    result = subprocess.run(  # noqa: S603 -- invoke test executable
        [executable, "install-skills", "--dest", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert (target / "thesis-writing" / "SKILL.md").is_file()
    assert (target / "thesis-review" / "SKILL.md").is_file()
    assert (target / "citation-checker" / "SKILL.md").is_file()
    assert "Installed thesis-writing" in result.stdout
    assert "Installed thesis-review" in result.stdout
    assert "Installed citation-checker" in result.stdout
