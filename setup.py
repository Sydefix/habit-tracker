from setuptools import find_packages, setup

setup(
    # metadata
    name="habit",
    version="0.1.0",
    description="A habit tracker project",
    author="Marouane TORY",
    author_email="marouane.tory@iu-study.org",
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    # dependencies
    install_requires=[
        "click>=8.0,<9.0",
        "SQLAlchemy>=2.0,<3.0",
    ],
    # optional dependencies
    extras_require={
        "dev": [
            "pytest",
        ],
    },
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # Adding console script
    entry_points={
        "console_scripts": [
            "habit = habit.cli:cli",
        ],
    },
)