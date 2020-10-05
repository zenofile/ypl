#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    readme = fh.read()

with open("requirements.txt", "rt") as f:
  requirements = f.read().splitlines()
  
setuptools.setup(
    name="ydlp", # Replace with your own username
    version="0.0.1",
    author="Thorsten Schubert",
    author_email="tschubert@bafh.org",
    description="Extract video URLs from YouTube's playlists using the Google API",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    entry_points={"console_scripts": ["ydlp = ydlp:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)