"""Exercise the CI dependency-install policy using harmless local source fixtures."""

import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

import pytest
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def uv():
    executable = os.environ.get("CI_BUILD_UV") or shutil.which("uv")
    if os.environ.get("CI_BUILD_INTEGRATION") != "1":
        pytest.skip("Run with CI_BUILD_INTEGRATION=1 and uv 0.13.8, as the Tests CI matrix does")
    assert executable
    assert subprocess.check_output([executable, "--version"], text=True).startswith("uv 0.13.8 ")
    return executable


def sync_script(workflow="tests.yml"):
    document = YAML(typ="safe").load((ROOT / ".github/workflows" / workflow).read_text())
    job = next(iter(document["jobs"].values()))
    return next(step["run"] for step in job["steps"] if step.get("name") == "Install dependencies")


def source_project(tmp_path, name, version="1.0.0", build_requirements=()):
    project = tmp_path / "project"
    project.mkdir()
    index = tmp_path / "index"
    index.mkdir()
    marker = tmp_path / "backend-executed"
    normalized = name.replace("-", "_")
    metadata = f"Metadata-Version: 2.3\nName: {name}\nVersion: {version}\n\nFixture\n"
    backend = f'''import pathlib, zipfile
def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    pathlib.Path({str(marker)!r}).write_text("executed")
    filename = "{normalized}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(pathlib.Path(wheel_directory) / filename, "w") as wheel:
        wheel.writestr("{normalized}-{version}.dist-info/METADATA", {metadata!r})
        wheel.writestr("{normalized}-{version}.dist-info/WHEEL", "Wheel-Version: 1.0\\nTag: py3-none-any\\n")
        wheel.writestr("{normalized}-{version}.dist-info/RECORD", "")
    return filename
'''
    with tarfile.open(index / f"{normalized}-{version}.tar.gz", "w:gz") as archive:
        for name_in_archive, content in {
            "PKG-INFO": metadata,
            "pyproject.toml": f'[build-system]\nrequires={json.dumps(list(build_requirements))}\nbuild-backend="backend"\nbackend-path=["."]\n',
            "backend.py": backend,
        }.items():
            data = content.encode()
            info = tarfile.TarInfo(f"{normalized}-{version}/{name_in_archive}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    (project / "pyproject.toml").write_text(
        '[project]\nname="policy-fixture"\nversion="0"\nrequires-python=">=3.11"\n'
        f"dependencies=[{json.dumps(name + '==' + version)}]\n"
        "[dependency-groups]\ndev=[]\ndocs=[]\n[tool.uv]\npackage=false\nno-index=true\n"
        f"find-links=[{json.dumps(str(index))}]\n"
    )
    return project, marker


def install(uv, project, workflow="tests.yml"):
    env = {
        "PATH": f"{Path(uv).parent}:{os.defpath}",
        "UV_PYTHON": sys.executable,
        "UV_PYTHON_DOWNLOADS": "never",
        "UV_CACHE_DIR": str(project.parent / "cache"),
        "UV_OFFLINE": "1",
    }
    # Static PKG-INFO supplies the lock metadata without executing the fixture backend.
    subprocess.run([uv, "lock", "--project", str(project)], env=env, check=True, capture_output=True, text=True)
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", sync_script(workflow)],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("workflow", ["tests.yml", "code_quality.yml", "docs.yml"])
def test_ci_rejects_an_unapproved_source_build_before_running_its_backend(tmp_path, uv, workflow):
    project, marker = source_project(tmp_path, "unexpected-source")
    result = install(uv, project, workflow)
    assert result.returncode != 0, result.stderr
    assert not marker.exists()


@pytest.mark.parametrize("name,version", [("qblox-instruments", "1.0.3"), ("marshmallow-polyfield", "5.11")])
def test_only_named_exceptions_can_build(tmp_path, uv, name, version):
    project, marker = source_project(tmp_path, name, version)
    result = install(uv, project)
    assert result.returncode == 0, result.stderr
    assert marker.read_text() == "executed"


def test_first_party_editable_build_remains_enabled(tmp_path, uv):
    project, marker = source_project(tmp_path, "first-party")
    with tarfile.open(tmp_path / "index/first_party-1.0.0.tar.gz") as archive:
        backend = archive.extractfile("first_party-1.0.0/backend.py").read().decode()
    (project / "backend.py").write_text(backend + "\nbuild_editable = build_wheel\n")
    (project / "pyproject.toml").write_text(
        '[project]\nname="first-party"\nversion="1.0.0"\nrequires-python=">=3.11"\n'
        '[build-system]\nrequires=[]\nbuild-backend="backend"\nbackend-path=["."]\n'
        "[dependency-groups]\ndev=[]\n"
    )
    result = install(uv, project)
    assert result.returncode == 0, result.stderr
    assert marker.exists()


def test_exception_cannot_resolve_an_unreviewed_build_dependency(tmp_path, uv):
    project, marker = source_project(tmp_path, "qblox-instruments", "1.0.3", ["builder-helper==1.0"])
    wheel = tmp_path / "index/builder_helper-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "builder_helper-1.0.dist-info/METADATA", "Metadata-Version: 2.3\nName: builder-helper\nVersion: 1.0\n"
        )
        archive.writestr("builder_helper-1.0.dist-info/WHEEL", "Wheel-Version: 1.0\nTag: py3-none-any\n")
        archive.writestr("builder_helper-1.0.dist-info/RECORD", "")
    result = install(uv, project)
    assert result.returncode != 0
    assert "hash" in result.stderr.lower(), result.stderr
    assert not marker.exists()


def test_exception_review_matches_locked_artifacts_and_every_ci_sync():
    policy = tomllib.loads((ROOT / ".github/ci-build-exceptions.toml").read_text())["exception"]
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    by_name = {package["name"]: package for package in lock["package"]}
    names = {exception["name"] for exception in policy}
    for exception in policy:
        package = by_name[exception["name"]]
        assert package["version"] == exception["version"], "Re-review the source-build exception after a version change"
        assert package["sdist"]["hash"] == exception["sdist-hash"]
        assert not package.get("wheels"), "Recheck whether this exception is still needed"
        assert exception["reason"]
    for workflow in ["tests.yml", "code_quality.yml", "docs.yml"]:
        flags = shlex.split(sync_script(workflow))
        allowed = {flags[index + 1] for index, flag in enumerate(flags) if flag == "--no-binary-package"}
        assert allowed == names


@pytest.mark.skipif(
    os.environ.get("CI_BUILD_VERSION_INTEGRATION") != "1", reason="Explicit networked build-version CI step"
)
def test_constrained_hatch_vcs_preserves_release_and_development_versions(tmp_path, uv):
    project = tmp_path / "version-fixture"
    (project / "src/qililab").mkdir(parents=True)
    (project / "src/qililab/__init__.py").write_text("")
    text = (ROOT / "pyproject.toml").read_text()
    build = text[text.index("[build-system]") : text.index("[tool.uv]")]
    constraints = text[text.index("[tool.uv]") : text.index("prerelease =")]
    (project / "pyproject.toml").write_text(
        '[project]\nname="qililab"\ndynamic=["version"]\nrequires-python=">=3.11"\n' + build + constraints
    )

    def git(*args):
        subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True)

    git("init", "--quiet")
    git("config", "user.name", "Version fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "commit.gpgsign", "false")
    git("add", ".")
    git("commit", "--quiet", "-m", "release")
    git("tag", "2.3.4")
    git("tag", "v99.0.0")
    for expected in ["qililab-2.3.4-", "qililab-2.3.5.dev1+"]:
        destination = tmp_path / expected
        env = dict(os.environ, UV_PYTHON=sys.executable, UV_CACHE_DIR=str(tmp_path / "cache"))
        result = subprocess.run(
            [
                uv,
                "build",
                "--directory",
                str(project),
                "--wheel",
                "--out-dir",
                str(destination),
                "--require-build-hashes",
                "--no-cache",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert next(destination.glob("*.whl")).name.startswith(expected)
        git("commit", "--quiet", "--allow-empty", "-m", "development")
        if expected == "qililab-2.3.4-":
            git("tag", "bsc-999")
