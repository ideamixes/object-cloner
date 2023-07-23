# pylint: disable=missing-docstring
import os
from setuptools import setup, find_packages

requirements_files = ["requirements.txt"]
if os.environ.get('OBJECT_CLONER_DEV_DEPENDENCIES_ENABLED') == 'true':
    requirements_files.append("requirements-dev.txt")
requirements = []
for filename in requirements_files:
    with open(filename, "r", encoding="utf-8") as f:
        requirements += f.read().strip().split("\n")

setup(
    name="objectcloner",
    version=os.environ['OBJECT_CLONER_VERSION'],
    author="IdeaMixes",
    author_email="mnasonov@ideamix.es",
    description="Object Cloner",
    license="MIT",
    # pylint: disable=consider-using-with
    long_description=(open("README.rst", "r", encoding="utf-8").read() if os.path.exists("README.rst") else ""),
    packages=find_packages(),
    install_requires=requirements,
    keywords=['kubernetes']
)
