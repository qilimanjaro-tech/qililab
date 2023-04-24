Pre-Requirements
+++++++++++++++++++++

Here are the essentials for installing and using qililab.

Python
===================
You should have `Python <https://www.python.org/downloads/>`_ installed properly to follow along with these prosses.
Having it installed properly refers to having it installed in your machine as well as having python added to your path, as well as pip.

.. caution:: Python version
    It is important to have python in a version superior to *Pyhton 3.Determinate*.

To verify that python is operational in your machine try executing it in your terminal:
::

   python --version

To verify pip is installed and on the path:
::

    pip install numpy

Virtual Environment
===================
As with python, it is important to have a tool to create virtual environments, `virtualenv <https://virtualenv.pypa.io/en/latest/>`_ is the program we will be using

To verify if it is installed correctly try:
::

    which virtualenv

You should get the directory from where it will be executed.

Git
=====================
Install `git <https://git-scm.com/downloads>`_ and configurated as follows:

create a .gitconfig file
::

    git config --global user.name "Name Surname"

once created, open the file in any editor you want and add these lines:


::

    [core]
	    excludesfile = /home/userPC/.gitignore
    [url "https://userGit:token@github.com"]
	    insteadOf = https://github.com
    [url "https://userGit:token@github.com/"]
	    insteadOf = git@github.com:

Do not copy directly these text, you may personalize the following lines:

* ``userPC`` should be changed to the name of the user on the machine
* ``userGit`` should be changed to de user name on your name account on GitHub
* ``token`` should be changed to your particular token that lets access to your GitHub through your machine. This process is explained in the next section.

.. note::
    As an archive beginning with a ``.``, it will be invisible. To edit you can open it from the terminal, with ``code .gitconfig``

Tokens
======

To create personal access tokens do the following steps:

#. Go to your GitHub profile
#. Settings
#. Developer settings
#. Personal access tokens
#. Tokens (classic)
#. Generate new token
#. Generate new token (classic)
#. In *note* you can type whatever you want (eg. the name of the machine 'personal Linux)
#. Set expiration to 90 days
#. In scopes select at least *repo*
#. Click generate token
#. Copy your token and paste it into the .gitconfig document
