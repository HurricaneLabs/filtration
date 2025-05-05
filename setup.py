from setuptools import setup


VERSION = "2.3.2"


with open("README.rst", "r") as f:
    long_description = f.read()


setup(
    name="filtration",
    version=VERSION,
    author="Steve McMaster",
    author_email="mcmaster@hurricanelabs.com",
    packages=["filtration"],
    description="filtration - A library for parsing arbitrary filters",
    long_description=long_description,
    install_requires=[
        "pyparsing>=3.0.0",
        "ipcalc"
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/HurricaneLabs/filtration/issues"
    }
)
