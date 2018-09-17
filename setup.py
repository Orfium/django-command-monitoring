from setuptools import setup, find_packages
from distutils.command.install import INSTALL_SCHEMES

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup(
    # Application name
    name="django_command_monitoring",

    # Version number
    version="0.1.2",

    # Application author details
    author="Konstantinos Siaterlis",
    author_email="siaterliskonsta@gmail.com",

    # Packages
    packages=find_packages(),

    # Details
    license="LICENSE",
    description="A toolset for monitoring django commands through FireBase.",

    # Dependent packages (distributions)
    install_requires=[
        "django>=1.11",
        "python-firebase",
    ],
)
