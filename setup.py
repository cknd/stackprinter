import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stackprinter",
    version="0.1.2",
    author="cknd",
    author_email="ck-github@mailbox.org",
    description="Prettier tracebacks & call stacks with variable values and colorful highlighting",
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