"""Installation script for python"""
import os

from setuptools import find_packages, setup

PACKAGE = "qililab"


with open("src/qililab/config/version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")


# Read in requirements
with open("requirements.txt", encoding="utf-8") as reqs_file:
    reqs = reqs_file.readlines()
requirements = [r.strip() for r in reqs]

# load long description from README
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name=PACKAGE,
    version=version,
    description="Fundamental package for fast characterization and calibration of quantum chips.",
    author="Qilimanjaro Quantum Tech",
    author_email="info@qilimanjaro.tech",
    url="https://github.com/qilimanjaro-tech/qililab",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["*.out"]},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    install_requires=requirements,
    python_requires=">=3.10.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache License 2.0",
)
