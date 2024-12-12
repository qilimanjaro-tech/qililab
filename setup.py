# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Installation script for python"""

import os
import site
import sysconfig

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


def _postprocess_setup():
    site_packages_paths = site.getsitepackages() or sysconfig.get_paths().get("purelib", [])
    if not site_packages_paths:
        return

    qm_init_path = os.path.join(site_packages_paths[0], "qm", "__init__.py")

    if os.path.exists(qm_init_path):
        with open(qm_init_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        if lines and lines[-1].startswith("logger.info"):
            lines = lines[:-1]

            with open(qm_init_path, "w", encoding="utf-8") as file:
                file.writelines(lines)


# Run postprocessing
_postprocess_setup()
