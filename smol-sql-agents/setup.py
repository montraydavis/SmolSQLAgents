from setuptools import setup, find_packages

setup(
    name="sql-doc-agent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai>=1.12.0",
        "numpy>=1.26.4",
        "tiktoken>=0.6.0",
        "vectordb>=0.0.21",
        "pytest>=8.0.0",
        "pytest-mock>=3.12.0",
        "tenacity>=8.0.0"
    ],
    python_requires=">=3.8"
)

from setuptools import setup, find_packages

setup(
    name="sql-doc-agent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai>=1.12.0",
        "numpy>=1.26.4",
        "tiktoken>=0.6.0",
        "vectordb>=1.0.0",
        "pytest>=8.0.0",
        "pytest-mock>=3.12.0",
        "tenacity>=8.0.0"
    ],
    python_requires=">=3.8",
)
