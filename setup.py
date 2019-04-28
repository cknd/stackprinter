import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stackprinter",
    version="0.1.6",
    author="cknd",
    author_email="ck-github@mailbox.org",
    description="Debug-friendly stack traces, with variable values and semantic highlighting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cknd/stackprinter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
