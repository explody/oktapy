import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "oktapy",
    version = "0.3",
    author = "Mike Culbertson",
    author_email = "mculbertson@pivotal.io",
    description = ("Very thin wrapper around Okta's API"),
    license = "BSD",
    keywords = "example documentation tutorial",
    url = "http://pivotal.io",
    packages=['oktapy'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: BSD License",
    ],
    data_files = [('/etc/oktapy', ['oktapy/okta-api.yml','oktapy/okta-objects.yml','okta.yml'])]
)
