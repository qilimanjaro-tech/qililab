# How to setup your local environment

This document describes the necessary steps to setup your local environment to be ready to start contributing to the project.

## Requirements

🛠 First of all, you need a minimum software/tools to do it:

- a shell terminal (with your desired shell: bash, zsh, etc.)
- 🐍  Python 3.10 or later
- git
- an account to github.com
- you github account linked to the Qilimanjaro github profile
- a code editor: nano, vim, PyCharm, VSCode, etc.

### Check your Python version

Open your terminal and run the following command:

```sh
python
```

It should look something like this:

```sh
❯ python
Python 3.10.0 (default, Mar  3 2022, 09:58:08) [GCC 7.5.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Check for the version next to `Python`.

If it is `3.10` or later, then you are ready to start. 🚀

In case your version, it is `2.X`, try `python3` instead of `python`.

If it is lower than `3.10`, then either you use a `conda` environment with that Python version (more details latter) or you install a Python `3.10` version in your system.

## Set a global gitignore

There are certain files created by particular editors, IDEs, operating systems, etc., that do not belong in a repository. But adding system-specific files to the repo's `.gitignore` is considered a poor practice. This file should only exclude files and directories that are a part of the package that should not be versioned as well as files that are generated (and regenerated) as artifacts of a build process.

Read the [How to set a Global Gitignore](./global_gitignore.md)

## Create a new project virtual environment

There are two ways to create a virtual environment, either using `virtualenv` or `conda`. If you are familiar with one of those, pick that first. In case you are on a macbook with the new M1 chip with ARM64 architecture, I recommend to follow the `conda` instructions.

### Using `virtualenv`

Open a new terminal and move to your base environment directory.

```sh
cd ~/environments
```

Create the new project environment with the following command:

Example for `your-project-environment-name` being `qililab`

```sh
python3 -m venv ~/environments/qililab
```

Whenever you want to use the `qililab` environment, just type:

```sh
source ~/environments/qililab/bin/activate
```

### Using `conda`

Open a new terminal and create the new `qililab` project environment with the following command:

```sh
conda create -n qililab python=3.10
```

> ℹ It may ask if you want to proceed with the installation of some libraries.

After completion, and whenever you want to use the `qililab` environment, just type:

```sh
conda activate qililab
```

## Clone the project repository and install the project library dependencies for development

Open a new terminal, move to a directory where you want to clone the repository and type:

```sh
git clone https://github.com/qilimanjaro-tech/qililab.git
```

> ⚠ Depending on your git account configuration you may need to input your git username and password or token.

Move to the new cloned project directory:

```sh
cd qililab
```

And with the virtual environment activated, install the required project libraries for development:

```sh
pip install -r dev-requirements.txt
```

At last, execute `pre-commit install` this will install git hooks in .git/ directory of the project.

```sh
pre-commit install
```

## Install the project library

On the project base directory, where you can see that there is a `setup.py` file, install the library as a development environment. Run the following command:

```sh
pip install -e .
```

### Check the flux qubit simulator is successfully installed

#### Python example

Start a new terminal and run the `example.py` script inside the `examples` folder:

```sh
python examples
```

### Jupyter notebook example

Run the `example.ipynb` notebook included in the `examples` folder using the kernel environment.

You should be able to import the library and instantiate a new object.
