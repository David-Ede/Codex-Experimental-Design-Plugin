from __future__ import annotations

from doe_toolchain import __version__
from doe_toolchain.server import dependency_versions


def test_backend_import_and_version_smoke() -> None:
    assert __version__ == "0.1.0"
    versions = dependency_versions()
    for package_name in [
        "mcp",
        "pydantic",
        "jsonschema",
        "numpy",
        "scipy",
        "pandas",
        "statsmodels",
        "scikit-learn",
        "pytest",
    ]:
        assert versions[package_name]
