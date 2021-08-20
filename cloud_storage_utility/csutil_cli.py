"""Root module for csutil CLI."""
import asyncio
import fnmatch
import glob
import logging
import os
import sys
from functools import update_wrapper

import click
from colorama import Fore, Style, init
from setuptools_scm import get_version
from tqdm import tqdm

from .common.cloud_local_map import CloudLocalMap
from .common.util import run
from .config.config import COS_CONFIG, DEFAULT_PLATFORM
from .file_broker import FileBroker

UNLIMITED_ARGS = -1
COUNT = 0

PROGRESS_BAR_COLOR = "blue"
PROGRESS_BAR_UNITS = "files"

DEBUG = os.getenv("DEBUG")
DESIRED_PLATFORM = os.getenv("CSUTIL_DEFAULT_PLATFORM")
CONFIG = COS_CONFIG[DEFAULT_PLATFORM]

init()
if DEBUG:
    logging.basicConfig(filename="csutil-error.log", level=logging.WARNING)
try:
    __version__ = get_version(root="..", relative_to=__file__)
except Exception:
    __version__ = "0.0.0"


_global_test_options = [
    click.option(
        "--fail-fast",
        "--failfast",
        "-f",
        "fail_fast",
        is_flag=True,
        default=False,
        help="Stop on failure",
    )
]


def __global_test_options(func):
    for option in reversed(_global_test_options):
        func = option(func)
    return func


def __filter_cloud_keys(wildcard_patterns, cloud_keys, prefix):
    filtered_keys = []
    if prefix == "":
        prefix = "*?"
    wildcard_patterns = [f"{prefix}{wildcard}" for wildcard in wildcard_patterns]
    for wildcard in wildcard_patterns:
        wildcard = wildcard.strip()
        filtered_keys += fnmatch.filter(cloud_keys, wildcard)
    return filtered_keys


def run_async(func):
    """
    Allows you to run a click command asynchronously.
    """
    func = asyncio.coroutine(func)

    def inner_handler(*args, **kwargs):
        run(func(*args, **kwargs))

    return update_wrapper(inner_handler, func)


def __local_file_exists(local_filepath):
    return os.path.exists(local_filepath)


def __add_if_file_exists(cloud_map_list, filepath):
    if __local_file_exists(filepath):
        cloud_map_list.append(CloudLocalMap(os.path.basename(filepath), filepath))
    else:
        print(
            f"{Fore.YELLOW}Warning: {filepath} could not be uploaded, it doesn't exist locally.{Style.RESET_ALL}"
        )


def __update_pbar_with_filenames(action, fail_fast, pbar, filename, succeeded):
    if pbar is None:
        return

    pbar.update()
    filename = filename
    if succeeded:
        pbar.write(
            f"{Fore.GREEN}{Style.BRIGHT}Success{Style.NORMAL}: {action}ed {filename}{Style.RESET_ALL}"
        )
    else:
        pbar.write(
            f"{Fore.RED}{Style.BRIGHT}Failed{Style.NORMAL}:  {action}ing {filename}{Style.RESET_ALL}"
        )
        if fail_fast:
            print(f"{Fore.RED}I give up{Style.RESET_ALL}")
            sys.exit(1)


def __update_pbar_remove(pbar, files_deleted):
    pbar.update(len(files_deleted))
    for file in files_deleted:
        pbar.write(
            f"{Fore.GREEN}{Style.BRIGHT}Success{Style.NORMAL}: deleted {file}{Style.RESET_ALL}"
        )


@click.group()
@click.version_option(__version__)
def execute_cli():
    """Interact with cloud storage from multiple cloud providers all through one CLI!"""
    pass


@execute_cli.command()
@click.argument("bucket-name", type=click.STRING)
@click.argument("cloud-key-wildcards", type=click.STRING, nargs=UNLIMITED_ARGS)
@click.option(
    "-p",
    "--prefix",
    type=click.STRING,
    help="Prefix to prepend the filename with in the cloud",
    default="",
)
@run_async
async def list_remote(bucket_name, cloud_key_wildcards, prefix):
    """List contents of cloud bucket."""
    async with FileBroker(CONFIG) as file_broker:
        keys = await file_broker.get_bucket_keys(bucket_name, prefix)
        if len(keys) == 0:
            print(f"No Keys found matching the prefix {prefix} in {bucket_name}")
        else:
            if len(cloud_key_wildcards) == 0:
                cloud_key_wildcards = ["*"]

            keys = __filter_cloud_keys(cloud_key_wildcards, keys, prefix)
            print(*keys, sep="\n")


@execute_cli.command()
@__global_test_options
@click.argument("cloud-bucket", type=click.STRING)
@click.argument("local-file-pattern", type=click.STRING, nargs=UNLIMITED_ARGS)
@click.option(
    "-p",
    "--prefix",
    type=click.STRING,
    help="Only push files with matching prefix",
    default="",
)
@run_async
async def push(fail_fast, local_file_pattern, cloud_bucket, prefix):
    """Push files from local machine to the cloud bucket."""
    patterns = list(local_file_pattern)
    cloud_map_list = []
    for pattern in patterns:
        pattern = pattern.strip()
        pattern_expansion = glob.glob(pattern, recursive=False)

        # Only try to upload files, exclude any directories
        pattern_expansion = list(
            filter(lambda path: os.path.isfile(path), pattern_expansion)
        )

        # Either the pattern expansion is a list of files, or it's a file itself
        if len(pattern_expansion) == 0:
            __add_if_file_exists(cloud_map_list, pattern)
        else:
            for filepath in pattern_expansion:
                __add_if_file_exists(cloud_map_list, filepath)

    if len(cloud_map_list) > 0:
        pbar = tqdm(
            total=len(cloud_map_list),
            desc="Uploading",
            unit=PROGRESS_BAR_UNITS,
            colour=PROGRESS_BAR_COLOR,
        )
        async with FileBroker(CONFIG) as file_broker:
            await file_broker.upload_files(
                cloud_bucket,
                cloud_map_list,
                prefix,
                lambda bucket_name, cloud_key, file_path, succeeded: __update_pbar_with_filenames(
                    "upload", fail_fast, pbar, file_path, succeeded
                ),
            )

        pbar.close()
    else:
        print("Nothing to push.")


@execute_cli.command()
@__global_test_options
@click.argument("cloud-bucket", type=click.STRING)
@click.argument("destination-dir", type=click.Path(exists=True, file_okay=False))
@click.argument("cloud-key-wildcards", type=click.STRING, nargs=UNLIMITED_ARGS)
@click.option(
    "-p",
    "--prefix",
    type=click.STRING,
    help="Only pull files with matching prefix",
    default="",
)
@run_async
async def pull(fail_fast, cloud_bucket, destination_dir, cloud_key_wildcards, prefix):
    """Pull files from the cloud bucket to the local machine.

    IMPORTANT: WRAP YOUR WILDCARDS IN QUOTES
    """
    # Get the names of all the files in the bucket
    async with FileBroker(CONFIG) as file_broker:
        bucket_contents = await file_broker.get_bucket_keys(cloud_bucket, prefix)
        # Filter out the ones we need
        keys_to_download = __filter_cloud_keys(
            cloud_key_wildcards, bucket_contents, prefix
        )

        if len(keys_to_download) > 0:
            pbar = tqdm(
                total=len(keys_to_download),
                desc="Downloading",
                unit="files",
                colour=PROGRESS_BAR_COLOR,
            )

            await file_broker.download_files(
                cloud_bucket,
                destination_dir,
                keys_to_download,
                prefix,
                lambda bucket_name, cloud_key, file_path, succeeded: __update_pbar_with_filenames(
                    "download", fail_fast, pbar, file_path, succeeded
                ),
            )

            pbar.close()
        else:
            print("No matching files found in the specified cloud bucket.")


@execute_cli.command()
@click.argument("cloud-bucket", type=click.STRING)
@click.argument("cloud-key-wildcards", type=click.STRING, nargs=UNLIMITED_ARGS)
@click.option(
    "-p",
    "--prefix",
    type=click.STRING,
    help="Only delete files with matching prefix",
    default="",
)
@run_async
async def delete(cloud_bucket, cloud_key_wildcards, prefix):
    """Delete files from the cloud bucket."""
    async with FileBroker(CONFIG) as file_broker:
        bucket_contents = await file_broker.get_bucket_keys(cloud_bucket, prefix)
        keys_to_delete = __filter_cloud_keys(
            cloud_key_wildcards, bucket_contents, prefix
        )

        if len(keys_to_delete) > 0:
            pbar = tqdm(
                total=len(keys_to_delete),
                desc="Deleting",
                unit="files",
                colour=PROGRESS_BAR_COLOR,
            )
            await file_broker.remove_items(
                cloud_bucket,
                keys_to_delete,
                lambda bucket_name, file_path: __update_pbar_remove(pbar, file_path),
            )
            pbar.close()
        else:
            print("No matching files found in the specified cloud bucket.")


def main():
    """Entry point."""
    execute_cli()


if __name__ == "__main__":
    main()
