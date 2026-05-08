"""
SmartStudy - AI-Powered Study Session Optimizer
Setup configuration for package installation.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="smartstudy",
    version="1.0.0",
    author="SmartStudy Team",
    author_email="team@smartstudy.dev",
    description="AI-Powered Study Session Optimizer and Focus Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/smartstudy/smartstudy",
    packages=find_packages(exclude=["tests*", "ml_training*", "docs*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "smartstudy=frontend.app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.css", "*.sql", "*.json"],
    },
)
