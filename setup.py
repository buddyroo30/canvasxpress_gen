"""
Setup configuration for CanvasXpress Generation System
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    requirements = []
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements

setup(
    name="canvasxpress-gen",
    version="1.0.0",
    author="Andrew K Smith, Isaac Neuhaus",
    author_email="andrew.smith@bms.com",
    description="Generate CanvasXpress visualizations from natural language using LLMs",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/buddyroo30/canvasxpress_gen",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "canvasxpress-gen=canvasxpress_gen.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "canvasxpress_gen": [
            "data/*.json",
            "data/*.txt",
            "data/*.md",
        ],
    },
    keywords=[
        "visualization",
        "data-science",
        "machine-learning",
        "natural-language-processing",
        "canvasxpress",
        "llm",
        "ai",
        "charts",
        "graphs",
    ],
    project_urls={
        "Bug Reports": "https://github.com/buddyroo30/canvasxpress_gen/issues",
        "Source": "https://github.com/buddyroo30/canvasxpress_gen",
        "Documentation": "https://github.com/buddyroo30/canvasxpress_gen/blob/main/README.md",
        "Paper": "https://osf.io/preprints/osf/kf2xp",
    },
)