from setuptools import setup

setup(
    name="freckle",
    version="0.1",
    description="Python client for the Freckle API",
    author="Peter Baumgartner",
    author_email="pete@lincolnloop.com",
    url="https://github.com/ipmb/freckle",
    py_modules=["freckle"],
    install_requires=[
        "httplib2",
        "pyyaml",
        "iso8601",
    ],
)
