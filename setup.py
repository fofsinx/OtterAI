from setuptools import setup
import os

try:
    with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
except FileNotFoundError:
    requirements = []

try:
    with open(os.path.join(os.path.dirname(__file__), "README.md")) as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ""

setup(
    name="cori-ai",
    version="0.1.2",
    description="An AI-powered code review assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="The Boring Human",
    author_email="human@theboring.human",
    url="https://github.com/theboringhumane/cori-ai",
    packages=['cori_ai'],
    install_requires=requirements,
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
    ],
)
