# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('../../'))

project = 'Feste'
copyright = '2023, Christian S. Perone'
author = 'Christian S. Perone'
release = '0.2.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    'sphinx.ext.githubpages',
    'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

html_last_updated_fmt = ""
html_sidebars = {'**': ['globaltoc.html']}

html_context = {
    "github_user": "perone",
    "github_repo": "feste",
    "github_version": "master",
    "doc_path": "docs/source",
    "default_mode": "light"
}



html_theme_options = {
    "logo": {
        "image_light": "_static/feste_logo.png",
        "image_dark": "_static/feste_logo.png",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/perone/feste",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "Twitter",
            "url": "https://twitter.com/tarantulae",
            "icon": "fa-brands fa-twitter",
        },
    ],
    "use_edit_page_button": False,
    "pygment_light_style": "tango",
    "pygment_dark_style": "tango",
    #"analytics": {
    #    "google_analytics_id": "G-XXXXXXXXXX",
    #}
}

html_show_sourcelink = False
