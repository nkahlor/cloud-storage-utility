import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cloud-storage-utility",
    author="Nick Kahlor",
    author_email="nkahlor@gmail.com",
    description="A multi-platform cloud storage utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AAInternal/cloud-storage-utility",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    scripts=["scripts/csutil"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=["setuptools_scm"],
    use_scm_version={
        "write_to_template": '__version__ = "{version}"',
    },
    install_requires=[
        "click",
        "python-dotenv",
        "aiohttp",
        "xmltodict",
        "tqdm",
        "colorama",
        "setuptools_scm",
    ],
    python_requires=">=3.6",
)
