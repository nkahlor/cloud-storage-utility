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
    packages=["cloud_storage_utility"],
    scripts=["scripts/csutil"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    setup_requires=["setuptools_scm"],
    install_requires=[
        "click",
        "setuptools",
        "wheel",
        "twine",
        "python-dotenv",
        "ibm-cos-sdk",
        "adal",
        "azure-mgmt-datalake-analytics",
        "azure-storage-file-datalake",
        "azure-datalake-store",
        "azure-identity",
    ],
    python_requires=">=3.6",
)
