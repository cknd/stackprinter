import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

test_requires = ["pytest", "numpy"]

setuptools.setup(
    python_requires=">=3.4",
    install_requires=["stack_data"],
    test_requires=test_requires,
    extras_require={
        'tests': test_requires,
    },
    name="stackprinter",
    version="0.2.3",
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
