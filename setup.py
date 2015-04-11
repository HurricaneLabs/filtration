from setuptools import setup, find_packages

version = "1.0.0"

long_description = """
`Github <https://github.com/HurricaneLabs/filtration>`_
-------------------------------------------------------
"""

setup(
    name = "filtration",
    version = version,
    description = "A collection of python logging extensions",
    long_description = long_description,
    url = "https://github.com/HurricaneLabs/filtration",
    author = "Steve McMaster",
    author_email = "mcmaster@hurricanelabs.com",
    package_dir = {"":"src"},
    packages = find_packages("src"),
)
