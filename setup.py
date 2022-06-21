"""Installation script for python"""
import os
import re

from setuptools import find_packages, setup

PACKAGE = "qililab"


def get_version():
    """Gets the version from the package's __init__ file
    if there is some problem, let it happily fail"""
    version_file_path = os.path.join("src", PACKAGE, "__init__.py")
    with open(version_file_path, "rt", encoding="utf-8") as version_file:
        initfile_lines = version_file.readlines()
    vsre = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        if mo_ := re.search(vsre, line, re.M):
            return mo_[1]


# Read in requirements
with open("requirements.txt", encoding="utf-8") as reqs_file:
    reqs = reqs_file.readlines()
requirements = [r.strip() for r in reqs]

# load long description from README
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="qilimanjaro-qililab",
    version=get_version(),
    description="A template repository to create a Qilimanjaro Python library",
    author="Qilimanjaro team",
    author_email="info@qilimanjaro.tech",
    url="https://github.com/qilimanjaro-tech/qililab",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["*.out"]},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    install_requires=requirements,
    extras_require={
        "docs": [
            "sphinx",
            "sphinx_rtd_theme",
            "recommonmark",
            "sphinxcontrib-bibtex",
            "sphinx_markdown_tables",
            "nbsphinx",
            "IPython",
        ],
        "tests": ["pytest"],
    },
    python_requires=">=3.10.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
