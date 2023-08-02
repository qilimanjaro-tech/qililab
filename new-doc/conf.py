# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import qililab

project = "Qililab"
copyright = "2023, Qilimanjaro"
author = "Qilimanjaro"
release = qililab.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc"]

extensions += [
    "sphinxawesome_theme.highlighting",
    # "sphinxawesome_theme.docsearch",  # TODO: Uncomment this when access to DocSearch!
    # To help you with the upgrade to version 5:
    # "sphinxawesome.deprecated",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinxawesome_theme"
html_static_path = ["_static"]
