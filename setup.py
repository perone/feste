from typing import List

import setuptools

development_requires: List[str] = [
    "pytest>=7.2.1",
    "mypy>=1.0.1",
    "flake8>=6.0.0",
    "pytest-cov>=4.0.0",
    "sphinx>=6.1.3",
    "pydata-sphinx-theme>=0.13.0",
    "sphinx-tabs>=3.4.1",
    "nbsphinx>=0.8.12",
    "ipykernel>=6.21.2",
    "isort>=5.12.0",
    "invoke>=2.0.0",
    "pydocstyle>=6.3.0",
    "twine>=4.0.2",
    "sphinx-autobuild>=2021.3.14",
    "ipywidgets>=8.0.4",
    "sphinxcontrib-bibtex>=2.5.0",
]

setuptools.setup(
    name="feste",
    version="0.2.0",
    author="Christian S. Perone",
    author_email="christian.perone@gmail.com",
    description="Scalable NLP compositions with graph optimizations.",
    long_description="Scalable NLP compositions with graph optimizations",
    long_description_content_type="text/markdown",
    url="https://github.com/perone/feste",
    install_requires=[
        "python-iso639>=2023.2.4",
        "jinja2>=3.1.2",
        "toolz>=0.12.0",
        "openai",
        "rich>=13.3.1",
        "dask>=2023.2.0",
        "toolz>=0.12.0",
        "cohere>=4.0.1",
        "cloudpickle>=2.2.1",
    ],
    extras_require={
        'dev': development_requires,
    },
    project_urls={
        "Bug Tracker": "https://github.com/perone/feste/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    include_package_data=True,
)
