#!/usr/bin/env python3

import os
import re
import setuptools

with open("README.md", "r") as f:
    readme = f.read()

with open("requirements.txt", "rt") as f:
    requirements = f.read().splitlines()

with open(os.path.join("ypl", "__init__.py"), "rt") as f:
    version = re.search('__version__ = "([^"]+)"', f.read()).group(1)

setuptools.setup(
    name="ypl",
    version=version,
    author="Thorsten Schubert",
    author_email="tschubert@bafh.org",
    description="Extract video URLs from YouTube's playlists using Google API",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    entry_points={"console_scripts": ["ypl = ypl.cli:main"]},
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Android",
    ],
    python_requires=">=3.8",
)
