from setuptools import setup


VERSION = "2.0.1"


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
        "pyparsing",
        "ipcalc"
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
    ],
    bugtrack_url="https://github.com/HurricaneLabs/filtration/issues",
)
