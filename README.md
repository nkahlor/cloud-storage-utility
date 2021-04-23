# Cloud Storage Utility

[![codecov](https://codecov.io/gh/nkahlor/cloud-storage-utility/branch/main/graph/badge.svg?token=JBO83HCV0T)](https://codecov.io/gh/nkahlor/cloud-storage-utility)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/cloud-storage-utility.svg)](https://pypi.python.org/pypi/cloud-storage-utility/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/)

A Python based cloud utility to help you transfer files to and from multiple cloud providers under one CLI/API.


Note: Support for Azure is experimental, first priority is IBM!

## Installation

```shell
pip install cloud-storage-utility
```

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

# You only need to set these if you intend to use azure
CSUTIL_AZURE_STORAGE_ACCOUNT_NAME=
CSUTIL_AZURE_TENANT_ID=
CSUTIL_AZURE_CLIENT_ID=
CSUTIL_AZURE_CLIENT_SECRET=

# You can also just include the connections string instead!
CSUTIL_AZURE_CONNECTION_STRING=

# set them all if you intend to use this tool for both platforms
```

By default, the CLI will attempt to use IBM
Note: for IBM, if `CSUTIL_IBM_API_KEY` is undefined, we will attempt to use `IBMCLOUD_API_KEY` instead.

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

### Python API

Example usage

```python
import asyncio
from cloud_storage_utility.file_broker import FileBroker

async def main():
    async with FileBroker() as file_broker:
        file_broker.download_files(
            bucket_name="test-bucket",
            local_directory="./data",
            file_names=["tmp.txt1", "tmp2.txt"],
        )

if __name__ == "__main__":
    asyncio.run(main)
```

## Developing Locally

We use `pipenv` to manage packages. If you don't already have it installed, make sure to install it via `pip install pipenv`.

We also use `python-dotenv` for managing env vars for local development, so you can create a .env file for yourself and set the relevant vars that way.

```shell
# You can use any python version, but I recommend 3.9
pipenv --python 3.9

# Gotta use the pre flag because of the code formatter
pipenv install --dev --pre
```

Now you're all set to start writing code!


https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-object-operations