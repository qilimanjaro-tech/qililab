"""Exercise publishing's shell interface without AWS or an upload."""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]


def publish_job():
    workflow = YAML(typ="safe").load((ROOT / ".github/workflows/publish.yml").read_text())
    return workflow["jobs"]["deploy-codeartifacts"]


def run_publication(tmp_path, *, dry_run=False, fail_check=False, fail_aws=""):
    """Run the workflow's real check/upload scripts with recording external tools."""
    tools = tmp_path / "tools"
    tools.mkdir()
    project = tmp_path / "release-tools-source/.github/release-tools"
    interpreter = project / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    recorder = """import json, os, pathlib, sys
with open(os.environ['CALLS'], 'a') as stream:
    stream.write(json.dumps({'tool': str(pathlib.Path(__file__).resolve()), 'args': sys.argv[1:]}) + '\\n')
if 'check' in sys.argv and os.environ.get('FAIL_CHECK') == '1':
    sys.exit(1)
if pathlib.Path(__file__).name == 'aws':
    if os.environ.get('FAIL_AWS') == sys.argv[2]:
        sys.exit(17)
    print('fixture-value')
"""
    for executable in (tools / "aws", interpreter):
        executable.write_text(f"#!{sys.executable}\n{recorder}")
        executable.chmod(0o755)
    # Refuse transient resolution. A test must never reach a real uvx or network.
    (tools / "uvx").write_text("#!/bin/sh\necho 'unexpected transient tool resolution' >&2\nexit 99\n")
    (tools / "uvx").chmod(0o755)
    dist = tmp_path / "dist"
    dist.mkdir()
    for artifact in ("fixture-1.0-py3-none-any.whl", "fixture-1.0.tar.gz"):
        (dist / artifact).write_text("fixture")
    calls = tmp_path / "calls.jsonl"
    env = {
        "PATH": f"{tools}:{os.defpath}",
        "RELEASE_TOOLS_DIR": str(project),
        "CALLS": str(calls),
        "FAIL_CHECK": str(int(fail_check)),
        "FAIL_AWS": fail_aws,
        "CA_DOMAIN": "fixture-domain",
        "CA_DOMAIN_OWNER": "000000000000",
        "CA_REPOSITORY": "fixture-repository",
    }
    result = None
    for step in publish_job()["steps"]:
        if step.get("name") not in ("List & validate distributions", "Publish to CodeArtifact"):
            continue
        if "if" in step:
            assert step["if"] == "${{ !inputs.dry_run }}"
            if dry_run:
                continue
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            break
    events = [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []
    return result, events, str(interpreter)


def test_check_and_upload_share_preinstalled_environment(tmp_path):
    result, events, interpreter = run_publication(tmp_path)
    assert result.returncode == 0, result.stderr
    twine = [event for event in events if event["tool"] == interpreter]
    assert [event["args"] for event in twine] == [
        ["-m", "twine", "check", "dist/fixture-1.0-py3-none-any.whl", "dist/fixture-1.0.tar.gz"],
        ["-m", "twine", "upload", "dist/fixture-1.0-py3-none-any.whl", "dist/fixture-1.0.tar.gz"],
    ]


def test_dry_run_checks_without_requesting_upload_credentials(tmp_path):
    result, events, interpreter = run_publication(tmp_path, dry_run=True)
    assert result.returncode == 0, result.stderr
    assert len(events) == 1
    assert events[0]["tool"] == interpreter
    assert events[0]["args"][2] == "check"


def test_invalid_distribution_stops_before_credentials_or_upload(tmp_path):
    result, events, interpreter = run_publication(tmp_path, fail_check=True)
    assert result.returncode == 1
    assert len(events) == 1
    assert events[0]["tool"] == interpreter
    assert events[0]["args"][2] == "check"


@pytest.mark.parametrize("operation,expected_calls", [("get-authorization-token", 2), ("get-repository-endpoint", 3)])
def test_failed_aws_request_stops_before_upload(tmp_path, operation, expected_calls):
    result, events, _ = run_publication(tmp_path, fail_aws=operation)
    assert result.returncode == 17
    assert len(events) == expected_calls
    assert events[-1]["args"][0:2] == ["codeartifact", operation]


def test_tool_checkout_does_not_follow_the_requested_historical_build_ref():
    # A historical build ref can predate the lock. Tool policy follows this workflow.
    workflow = YAML(typ="safe").load((ROOT / ".github/workflows/publish.yml").read_text())
    build_checkout = workflow["jobs"]["build"]["steps"][0]
    tools_checkout = next(step for step in publish_job()["steps"] if step.get("name") == "Check out release tools")
    assert build_checkout["with"]["ref"] == "${{ inputs.ref || github.ref }}"
    assert tools_checkout["with"]["ref"] == "${{ github.workflow_sha }}"
    assert tools_checkout["with"]["persist-credentials"] is False


@pytest.fixture(scope="module")
def tool_uv():
    if os.environ.get("RELEASE_TOOLS_INTEGRATION") != "1":
        pytest.skip("The dedicated release-tools CI job runs pinned-uv installation tests")
    executable = shutil.which("uv")
    assert executable is not None
    version = subprocess.check_output([executable, "--version"], text=True)
    assert version.startswith("uv 0.13.8 "), version
    assert sys.version_info[:2] == (3, 13)
    return executable


def copy_tool_project(directory):
    directory.mkdir()
    for name in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(ROOT / ".github/release-tools" / name, directory / name)
    return directory


def uv_environment(executable, project, *, offline=False):
    return {
        "PATH": f"{Path(executable).parent}:{os.defpath}",
        "RELEASE_TOOLS_DIR": str(project),
        "UV_PYTHON": sys.executable,
        "UV_PYTHON_DOWNLOADS": "never",
        "UV_CACHE_DIR": str(project.parent / f"{project.name}-cache"),
        "UV_NO_PROGRESS": "1",
        "UV_OFFLINE": str(int(offline)),
    }


def install_tools(executable, project, *, offline=False):
    step = next(step for step in publish_job()["steps"] if step.get("name") == "Install release tools")
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=project.parent,
        env=uv_environment(executable, project, offline=offline),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


@pytest.fixture(scope="module")
def fresh_installations(tmp_path_factory, tool_uv):
    directory = tmp_path_factory.mktemp("release-tools")
    projects = [copy_tool_project(directory / name) for name in ("first", "second")]
    for project in projects:
        lock = (project / "uv.lock").read_bytes()
        result = install_tools(tool_uv, project)
        assert result.returncode == 0, result.stderr
        assert (project / "uv.lock").read_bytes() == lock
    return projects


def test_fresh_lock_installs_identical_tool_versions(fresh_installations):
    versions = []
    for project in fresh_installations:
        output = subprocess.check_output(
            [
                str(project / ".venv/bin/python"),
                "-c",
                "import importlib.metadata as m, json; "
                "print(json.dumps(sorted((d.metadata['Name'].lower(), d.version) for d in m.distributions())))",
            ],
            text=True,
        )
        versions.append(json.loads(output))
    assert versions[0] == versions[1]
    assert ["twine", "7.0.0"] in versions[0]
    assert "qililab" not in {name for name, _ in versions[0]}
    assert "pytest" not in {name for name, _ in versions[0]}


@pytest.mark.parametrize("missing", [False, True], ids=["stale", "missing"])
def test_unusable_lock_fails_without_rewriting(tmp_path, tool_uv, missing):
    project = copy_tool_project(tmp_path / "project")
    lock = project / "uv.lock"
    if missing:
        lock.unlink()
    else:
        manifest = project / "pyproject.toml"
        manifest.write_text(manifest.read_text().replace("twine==7.0.0", "twine==0.0.0"))
    before = lock.read_bytes() if lock.exists() else None
    result = install_tools(tool_uv, project, offline=True)
    assert result.returncode != 0
    assert (lock.read_bytes() if lock.exists() else None) == before


def test_tampered_wheel_hash_fails_closed(tmp_path, tool_uv):
    project = copy_tool_project(tmp_path / "project")
    lock = project / "uv.lock"
    lock.write_text(re.sub(r"sha256:[0-9a-f]{64}", "sha256:" + "0" * 64, lock.read_text()))
    before = lock.read_bytes()
    result = install_tools(tool_uv, project)
    assert result.returncode != 0
    assert "hash mismatch" in result.stderr.lower(), result.stderr
    assert lock.read_bytes() == before


def write_sdist(path, files):
    with tarfile.open(path, "w:gz") as archive:
        root = path.name.removesuffix(".tar.gz")
        directory = tarfile.TarInfo(root)
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(f"{root}/{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def test_source_only_requirement_cannot_execute_backend(tmp_path, tool_uv):
    project = tmp_path / "project"
    project.mkdir()
    index = tmp_path / "index"
    index.mkdir()
    sentinel = tmp_path / "backend-executed"
    write_sdist(
        index / "source_only-1.0.tar.gz",
        {
            "PKG-INFO": "Metadata-Version: 2.3\nName: source-only\nVersion: 1.0\n\nFixture\n",
            "pyproject.toml": '[build-system]\nrequires=[]\nbuild-backend="backend"\nbackend-path=["."]\n',
            "backend.py": f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n",
        },
    )
    (project / "pyproject.toml").write_text(
        '[project]\nname="fixture-project"\nversion="0"\nrequires-python=">=3.13,<3.14"\n'
        'dependencies=["source-only==1.0"]\n[tool.uv]\npackage=false\nno-index=true\n'
        f"find-links=[{json.dumps(str(index))}]\n"
    )
    # The fixture has static sdist metadata. Creating its lock must not execute its backend.
    locked = subprocess.run(
        [tool_uv, "lock", "--project", str(project)],
        env=uv_environment(tool_uv, project, offline=True),
        capture_output=True,
        text=True,
        check=False,
    )
    assert locked.returncode == 0, locked.stderr
    assert not sentinel.exists()
    result = install_tools(tool_uv, project, offline=True)
    assert result.returncode != 0
    assert "source-only" in result.stderr
    assert not sentinel.exists()


def test_real_twine_checks_wheel_and_sdist_and_rejects_invalid_metadata(tmp_path, fresh_installations):
    metadata = (
        "Metadata-Version: 2.3\nName: fixture\nVersion: 1.0\nSummary: Release fixture\n"
        "Description-Content-Type: text/plain\n\nFixture description.\n"
    )
    wheel = tmp_path / "fixture-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("fixture-1.0.dist-info/METADATA", metadata)
        archive.writestr("fixture-1.0.dist-info/WHEEL", "Wheel-Version: 1.0\nTag: py3-none-any\n")
        archive.writestr("fixture-1.0.dist-info/RECORD", "")
    sdist = tmp_path / "fixture-1.0.tar.gz"
    write_sdist(sdist, {"PKG-INFO": metadata})
    python = str(fresh_installations[0] / ".venv/bin/python")
    result = subprocess.run([python, "-m", "twine", "check", str(wheel), str(sdist)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("fixture-1.0.dist-info/METADATA", "Metadata-Version: 2.3\n")
    result = subprocess.run([python, "-m", "twine", "check", str(wheel)], capture_output=True, text=True)
    assert result.returncode != 0
