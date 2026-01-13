"""
Setup script for football-analytics-serverless package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="football-analytics-serverless",
    version="1.0.0",
    author="Adebayo Oyeleye",
    author_email="Adebayo.I.Oyeleye@student.shu.ac.uk",
    description="Scalable Live Data Processing for Football Analytics using Serverless Computing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/football-analytics-serverless",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.3.3",
            "pytest-cov>=5.0.0",
            "black>=24.10.0",
            "flake8>=7.1.1",
            "mypy>=1.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "football-analytics=scripts.run_local:main",
        ],
    },
)
