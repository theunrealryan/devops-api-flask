from setuptools import setup

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="taskboard",
    version="0.1.0",
    description="A simple task-board API built with Flask",
    author="Ryan Ricardo de Souza",
    author_email="you@example.com",
    url="https://gitlab.com/devops-api-flask/devops-api-flask",
    py_modules=["app"],
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Flask",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
