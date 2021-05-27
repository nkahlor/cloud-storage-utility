"""Routes cloud storage operations to underlying platform implementations."""

import asyncio
import os
import sys
from itertools import groupby
from typing import Callable, Dict, List, Union

import aiohttp

from .common.cloud_local_map import CloudLocalMap
from .config import config
from .platforms.ibm_cloud_storage import IbmCloudStorage
from .types.bucket_key import BucketKeyMetadata
from .types.ibm_configuration import IbmConfiguration


class FileBroker:
    """
    Executes file operations with the specified underlying platform implementation.

    This is implemented as an async context manager, due to the underlying need to manage aiohttp sessions.

    There are 2 ways to use this class:

    The ideal way is to use `async with` syntax, don't forget to use the `async` keyword, it's important!
    ```
    async with FileBroker(config) as file_broker:
        file_broker.upload_files(...)
    ```

    Alternatively, you can manually call  `open` and `close` to manage the http connections.

    ```
    file_broker = FileBroker()
    file_broker.open()

    file_broker.upload_files(...)

    file_broker.close()
    ```

    Generally, you only really want 1 file broker per application. You don't really need to open a ton of http sessions
    if you're connecting to the same host each time.
    """

    def __init__(
        self,
        configuration: Union[IbmConfiguration],
        platform: str = config.DEFAULT_PLATFORM,
    ):
        self.platform = platform
        self.config = configuration
        self.session = None
        self.service = None

    async def __aenter__(self):
        self.session = await self.__create_aiohttp_session()

        if self.platform == config.SupportedPlatforms.IBM:
            self.service = IbmCloudStorage(self.session, self.config)
        else:
            raise Exception("Cloud platform not supported")

        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def __create_aiohttp_session(self):
        return aiohttp.ClientSession(trust_env=True)

    async def __gather_results(self, tasks):
        results = []
        for i in range(0, len(tasks), self.config.batch_limit):
            results += await asyncio.gather(*tasks[i : i + self.config.batch_limit])
        return results

    async def open(self):
        """Open an aiohttp session"""
        return await self.__aenter__()

    async def close(self):
        """Close the aiohttp session"""
        await self.__aexit__(*sys.exc_info())

    async def get_bucket_keys(
        self, bucket_name: str, prefix: str = ""
    ) -> Dict[str, BucketKeyMetadata]:
        """Get the names of all the keys in the bucket.

        Args:
            bucket_name(str): The target bucket
            prefix(str, optional): Only return keys matching this prefix

        Returns:
            List of keys from the targeted bucket
        """
        return await self.service.get_bucket_keys(bucket_name, prefix)  # type: ignore

    async def upload_files(
        self,
        bucket_name: str,
        cloud_map_list: List[CloudLocalMap],
        prefix: str = "",
        callback: Callable[[str, str, str, bool], None] = None,
    ) -> None:
        """Upload a list of files from a local directory, and map them to they respective cloud keys in a particular bucket.

        Args:
            bucket_name (str):
                The target bucket.
            cloud_map_list (CloudLocalMap[]):
                List of local files to upload, and what to name them in the cloud.
            prefix (str, optional):
                Prefix to prepend in the cloud.
            callback (function, optional):
                Optional callback to execute after every file upload completes.
                Takes the parameters: bucket_name, cloud_key, file_path, removal_succeeded.
                Defaults to None.
        """
        upload_tasks = self.service.get_upload_files_coroutines(  # type: ignore
            bucket_name, cloud_map_list, prefix, callback
        )
        await self.__gather_results(upload_tasks)

    async def download_files(
        self,
        bucket_name: str,
        local_directory: str,
        file_names: List[str],
        prefix: str = "",
        callback: Callable[[str, str, str, bool], None] = None,
    ) -> None:
        """Download all of the requested files from the bucket, and place them in the specified directory.

        Args:
            bucket_name (str):
                Target bucket.
            local_directory (str):
                The destination folder. Must already exist.
            file_names (str[]):
                A list of the files we want to download.
            prefix (str, optional):
                Only download files with the matching prefix.
            callback (function, optional):
                Optional callback to execute after every file download completes.
                Takes the parameters: bucket_name, cloud_key, file_path, download_succeeded.
                Defaults to None.
        """
        download_tasks = self.service.get_download_files_coroutines(  # type: ignore
            bucket_name, local_directory, file_names, prefix, callback
        )
        await self.__gather_results(download_tasks)

    async def remove_items(
        self,
        bucket_name: str,
        cloud_keys: List[str],
        callback: Callable[[str, str, str], None] = None,
    ) -> None:
        """Remove the specified keys from the bucket. Does not remove local files.

        Args:
            bucket_name (str):
                Target bucket
            cloud_keys (str[]):
                Keys to remove from the cloud
            callback (function, optional):
                Optional callback to execute after every remove request completes.
                Takes the parameters: bucket_name, cloud_key, file_path.
                Defaults to None.
        """

        remove_tasks = self.service.get_remove_items_coroutines(  # type: ignore
            bucket_name, cloud_keys, callback
        )
        await self.__gather_results(remove_tasks)

    async def sync_local_files(
        self,
        file_paths: List[str],
        bucket_name: str,
        prefix: str = "",
    ) -> None:
        """If any of the files in file_paths are missing locally, go get them from the cloud bucket.

        We assume the name of a file in a file path is the same as the name of the file we want to download.

        Args:
            file_path (str[]):
                List of local file paths you want to synchronize.
            bucket_name (str):
                Target bucket.
            prefix(str, optional):
                Only sync files with the matching prefix.
        """

        # Exclude all files that exist locally
        missing_files = list(
            filter(lambda file_path: not os.path.exists(file_path), file_paths)
        )

        # Sort into groups based on where the files are on the local disk
        download_groups = groupby(
            missing_files, lambda file_path: os.path.dirname(file_path)
        )

        # Download every missing file to the correct local path
        for key, group in download_groups:
            group_as_list = list(group)
            cloud_keys = list(
                map(lambda file_path: os.path.basename(file_path), group_as_list)
            )
            await self.download_files(
                bucket_name=bucket_name,
                local_directory=key,
                file_names=cloud_keys,
                prefix=prefix,
                callback=None,
            )
