from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup


def read_version() -> str:
    # qlog/__init__.py defines __version__
    import re

    version_file = Path(__file__).parent / "qlog" / "__init__.py"
    m = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]\s*$", version_file.read_text(), re.M)
    if not m:
        raise RuntimeError("Unable to find __version__ in qlog/__init__.py")
    return m.group(1)


README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="qlog-cli",
    version=read_version(),
    description="Lightning-fast local log search and analysis",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Cosmo",
    url="https://github.com/Cosm00/qlog",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=[
        "rich>=13.0.0",
        "click>=8.0.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "qlog=qlog.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
    ],
)
