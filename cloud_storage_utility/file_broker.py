"""Routes cloud storage operations to underlying platform implementations."""

import asyncio
from cloud_storage_utility.common.base_cloud_storage import BaseCloudStorage
from cloud_storage_utility.common.cloud_local_map import CloudLocalMap
import os
from itertools import groupby
from typing import Callable, List

from .config import config
from .platforms.azure_cloud_storage import AzureCloudStorage
from .platforms.ibm_cloud_storage import IbmCloudStorage


class FileBroker:
    """Executes file operations with the specified underlying platform implementation."""

    def __init__(self, platform: str = config.DEFAULT_PLATFORM):
        """Initialize service with specified platform. Defaults to IBM, because why not?"""
        self.platform = platform
        if platform == config.SupportedPlatforms.IBM:
            self.service: BaseCloudStorage = IbmCloudStorage()
        elif platform == config.SupportedPlatforms.AZURE:
            self.service = AzureCloudStorage()
        else:
            raise Exception("Cloud platform not supported")

    def get_bucket_keys(self, bucket_name: str) -> List[str]:
        """Get the names of all the keys in the bucket.

        Args:
            bucket_name(str): The target bucket

        Returns:
            List of keys from the targeted bucket
        """
        return self.service.get_bucket_keys(bucket_name)

    def upload_files(
        self,
        bucket_name: str,
        cloud_map_list: List[CloudLocalMap],
        callback: Callable[[str, str, str, bool], None] = None,
    ) -> None:
        """Upload a list of files from a local directory, and map them to they respective cloud keys in a particular bucket.

        Args:
            bucket_name (str):
                The target bucket.
            cloud_map_list (CloudLocalMap[]):
                List of local files to upload, and what to name them in the cloud.
            callback (function, optional):
                Optional callback to execute after every file upload completes.
                Takes the parameters: bucket_name, cloud_key, file_path, removal_succeeded.
                Defaults to None.
        """
        loop = asyncio.get_event_loop()

        upload_tasks = self.service.get_upload_files_coroutines(
            bucket_name, cloud_map_list, callback
        )
        loop.run_until_complete(asyncio.gather(*upload_tasks))
        loop.close()

    def download_files(
        self,
        bucket_name: str,
        local_directory: str,
        file_names: List[str],
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
            callback (function, optional):
                Optional callback to execute after every file download completes.
                Takes the parameters: bucket_name, cloud_key, file_path, download_succeeded.
                Defaults to None.
        """
        loop = asyncio.get_event_loop()
        download_tasks = self.service.get_download_files_coroutines(
            local_directory, bucket_name, file_names, callback
        )
        loop.run_until_complete(asyncio.gather(*download_tasks))
        loop.close()

    def remove_items(
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

        loop = asyncio.get_event_loop()
        remove_tasks = self.service.get_remove_items_coroutines(
            bucket_name, cloud_keys, callback
        )
        loop.run_until_complete(asyncio.gather(*remove_tasks))
        loop.close()

    def sync_local_files(self, file_paths: List[str], bucket_name: str) -> None:
        """If any of the files in file_paths are missing locally, go get them from the cloud bucket.

        We assume the name of a file in a file path is the same as the name of the file we want to download.

        Args:
            file_path (str[]):
                List of local file paths you want to synchronize.
            bucket_name (str):
                Target bucket.
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
            self.download_files(
                bucket_name=bucket_name,
                local_directory=key,
                file_names=cloud_keys,
                callback=None,
            )