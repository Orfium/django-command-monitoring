from setuptools import setup, find_packages
from distutils.command.install import INSTALL_SCHEMES

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except:
    long_description = ''

setup(
    # Application name
    name="django_command_monitor",

    # Version number
    version="0.2.3",

    # Application author details
    author="Konstantinos Siaterlis",
    author_email="siaterliskonsta@gmail.com",

    # Packages
    packages=find_packages(),

    # Details
    license="LICENSE",
    description="A toolset for monitoring django commands through FireBase.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/Orfium/django-command-monitoring',

    # Dependent packages (distributions)
    install_requires=[
        "django>=1.11",
        "python-firebase",
    ],
)
