# Cloud Storage Utility

[![codecov](https://codecov.io/gh/nkahlor/cloud-storage-utility/branch/main/graph/badge.svg?token=JBO83HCV0T)](https://codecov.io/gh/nkahlor/cloud-storage-utility)

A Python based cloud utility to help you transfer files to and from multiple cloud providers under one CLI/API.

## Usage

#### Configuration

To configure this application, you have to set a few environment variables.

```
# You can use 'azure' or 'ibm'
CSUTIL_CLOUD_PLATFORM=

# You only need to set these if you intend to use ibm
CSUTIL_IBM_API_KEY=
CSUTIL_IBM_AUTH_ENDPOINT=
CSUTIL_IBM_COS_ENDPOINT=
CSUTIL_IBM_CRN=

# You only need to set these if you intend to use azure
CSUTIL_AZURE_STORAGE_ACCOUNT_NAME=
CSUTIL_AZURE_TENANT_ID=
CSUTIL_AZURE_CLIENT_ID=
CSUTIL_AZURE_CLIENT_SECRET=

# set them all if you intend to use this tool for both platforms
```

By default, the CLI will attempt to use IBM

#### CLI Commands

You can use `csutil --help` to see an exhaustive list of options and commands

```
csutil delete <bucket name> <filename>
csutil list-remote <bucket name>
csutil pull <bucket name> <destination directory>  <cloud-files>
csutil push <bucket name> <local-files>
```

Here are some examples

```
csutil delete example-bucket *.txt
csutil delete example-bucket *.txt *.md example.csv

csutil list-remote example-bucket

csutil pull example-bucket ./dat *
csutil pull example-bucket ./dat tmp.txt tmp2.txt *.md

csutil push example-bucket ./dat/*
csutil push example-bucket/test_directory ./dat/tmp.txt ./dat/tmp2.txt
```

## Developing Locally

We use `pipenv` to manage packages. If you don't already have it installed, make sure to install it via `pip install pipenv`.

We also use `python-dotenv` for managing env vars for local development, so you can create a .env file for yourself and set the relevant vars that way.

## Deploy to pypi

Make sure you have the venv activated `pipenv shell`

Build `python3 setup.py sdist bdist_wheel`

Deploy `python3 -m twine upload --repository testpypi dist/*`

Here's a good sample of a similar project https://github.com/pypa/sampleproject

## Additional Resources

- [InnerSource Marketplace](https://github.com/AAInternal/InnerSource-Marketplace)
- [Meta](https://github.com/AAInternal/meta)
- [TechRadar](https://github.com/AAInternal/TechRadar)
- [Sourcerer.io](https://github.com/sourcerer-io/sourcerer-app#readme)
