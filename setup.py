from setuptools import setup, find_packages

setup(
    name="qlog",
    version="0.1.0",
    description="Lightning-fast local log search and analysis",
    author="Cosmo",
    packages=find_packages(),
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
)
