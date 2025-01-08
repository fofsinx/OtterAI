"""Setup script for cori_ai."""
from setuptools import setup, find_packages

# Read long description from README
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "AI-powered code review and fix generation"

# Read requirements
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = []

setup(
    name="otterai",
    version="0.1.0",
    author="Harsh Vardhan Goswami",
    author_email="harshvardhan.goswami@gmail.com",
    description="AI-powered code review and fix generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harshvardhangoswami/otterai",
    packages=find_packages(include=["otterai", "cori_ai.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    tests_require=[
        "pytest>=7.4.0",
        "pytest-asyncio>=0.23.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
    ],
    entry_points={
        "console_scripts": [
            "otterai=cori_ai.__main__:main",
        ],
    },
) 