import abc
import os
from typing import Any, Callable, Coroutine, Dict, List

from ..common.cloud_local_map import CloudLocalMap
from ..common.util import strip_prefix
from ..types.bucket_key import BucketKeyMetadata

# 5 MB chunks
DEFAULT_PART_SIZE = 1024 * 1024 * 5

# 15 MB threshold
DEFAULT_FILE_THRESHOLD = 1024 * 1024 * 15


class BaseCloudStorage(metaclass=abc.ABCMeta):
    """
    Abstract definition of what a platform implementation needs to include. Any new platforms need to
    inherit from this.
    """

    def __init__(
        self,
        part_size: int = DEFAULT_PART_SIZE,
        file_threshold: int = DEFAULT_FILE_THRESHOLD,
    ):
        """Sets up platform independent configurations, and operations.

        Args:
            part_size (int, optional):
                The size of the chunks (how to divide up large files). Defaults to 5MB.
            file_threshold (int, optional):
                How large a file needs to be before performing operations in chunks. Defaults to 15MB.
        """
        super().__init__()

        self.part_size = part_size
        self.file_threshold = file_threshold

    @abc.abstractmethod
    async def get_bucket_keys(
        self, bucket_name: str, prefix: str = ""
    ) -> Dict[str, BucketKeyMetadata]:
        """An implementation of this must provide a way to list the contents of a bucket.

        Args:
            bucket_name (str):
                Target bucket.
            prefix (str, optional):
                Only get keys that match this prefix.

        Returns:
            Dict[str, BucketKeyMetadata]:
                Dictionary of key name -> KeyMetadata, i.e.

            ```
            {
                "image.jpeg": {
                    "bytes": 32,
                    "last_modified": 1619195172
                },
                "file.txt": {
                    "bytes": 32,
                    "last_modified": 1619195172
                }
            }
            ```

        """
        return {}

    @abc.abstractmethod
    async def upload_file(
        self,
        bucket_name: str,
        cloud_key: str,
        file_path: str,
        prefix: str = "",
        callback: Callable[[str, str, str, bool], None] = None,
    ) -> bool:
        """An implementation of this must provide a way to upload a single file, with a specified prefix.

        Args:
            bucket_name (str):
                Target bucket.
            cloud_key (str):
                What to name the file in the cloud.
            file_path (str):
                Where to get the file from locally.
            prefix (str, optional):
                Prefix to prepend in the cloud.
            callback (function, optional):
                Implementations of this method need to call this after the operation is complete. Defaults to None.

        Returns:
            bool:
                Whether the upload was successful or not.
        """
        return False

    def get_upload_files_coroutines(
        self,
        bucket_name: str,
        cloud_map_list: List[CloudLocalMap],
        prefix: str = "",
        callback: Callable[[str, str, str, bool], None] = None,
    ) -> List[Coroutine[Any, Any, bool]]:
        """Collect all of the coroutines necessary to complete the requested uploads.

        Args:
            bucket_name (str):
                Target bucket.
            cloud_map_list (List[CloudLocalMap]):
                List of local to remote file name pairings.
            prefix (str, optional):
                Prefix to apply to every file we upload.
            callback (function, optional):
                Passes the callback into each coroutine. Defaults to None.

        Returns:
            List[Coroutine[Any, Any, None]]:
                List of coroutines which will fulfill the operation.
        """

        upload_tasks = []
        for file in cloud_map_list:
            upload_tasks.append(
                self.upload_file(
                    bucket_name,
                    file.cloud_key,
                    file.local_filepath,
                    prefix,
                    callback,
                )
            )

        return upload_tasks

    @abc.abstractmethod
    async def remove_item(
        self,
        bucket_name: str,
        cloud_key: str,
        callback: Callable[[str, str, str], None] = None,
    ) -> bool:
        """An implementation for this must provide a way to send removal requests.

        Args:
            bucket_name (str):
                Target bucket.
            cloud_key (str):
                The name of the key we want to remove.
            callback (Callable[[str, str, str], None], optional):
                Implementations of this method need to call this after the operation is complete. Defaults to None.

        Returns:
            bool:
                Whether the remove was successful or not.
        """
        return False

    def get_remove_items_coroutines(
        self,
        bucket_name: str,
        item_names: List[str],
        callback: Callable[[str, str, str], None] = None,
    ) -> List[Coroutine[Any, Any, None]]:
        """Get a list of all the coroutines needed to perform the requested removal.

        Args:
            bucket_name (str):
                Target bucket.
            item_names (List[str]):
                Items to remove from the bucket.
            callback (Callable[[str, str, str], None], optional):
                Passes the callback into each coroutine. Defaults to None.

        Returns:
            List[Coroutine[Any, Any, None]]:
                List of coroutines which will fulfill the operation.
        """

        remove_tasks: List[Any] = []
        for item in item_names:
            remove_tasks.append(
                self.remove_item(
                    bucket_name=bucket_name,
                    cloud_key=item,
                    callback=callback,
                )
            )
        return remove_tasks

    @abc.abstractmethod
    async def download_file(
        self,
        bucket_name: str,
        cloud_key: str,
        destination_filepath: str,
        prefix: str = "",
        callback: Callable[[str, str, str, bool], None] = None,
    ) -> bool:
        """An implementation for this must provide a way to download a single file.

        Args:
            bucket_name (str):
                Target bucket.
            cloud_key (str):
                The name of the item we want to download from the cloud bucket.
            destination_filepath (str):
                Where to put the downloaded item.
            prefix (str, optional):
                Only download files under the matching prefix.
            callback (Callable[[str, str, str, bool], None], optional):
                Implementations of this method need to call this after the operation is complete. Defaults to None.

        Returns:
            bool:
                Whether the download was successful or not.
        """
        return False

    def get_download_files_coroutines(
        self,
        bucket_name: str,
        local_directory: str,
        cloud_key_list: List[str],
        prefix: str = "",
        callback: Callable[[str, str, str, bool], None] = None,
    ) -> List[Coroutine[Any, Any, bool]]:
        """Get a list of all the coroutines needed to perform the requested download.

        Args:
            bucket_name (str):
                Target bucket.
            local_directory (str):
                Where to put the files downloaded.
            cloud_key_list (List[str]):
                List of cloud keys to download.
            prefix (str, optional):
                Prefix to apply to every file we download.
            callback (Callable[[str, str, str, bool], None], optional):
                Implementations of this method need to call this after the operation is complete. Defaults to None.

        Returns:
            List[Coroutine[Any, Any, None]]:
                List of coroutines which will fulfill the operation.
        """

        download_tasks = []
        for item in cloud_key_list:
            download_tasks.append(
                self.download_file(
                    bucket_name=bucket_name,
                    cloud_key=item,
                    destination_filepath=os.path.join(
                        local_directory, strip_prefix(item, prefix)
                    ),
                    prefix=prefix,
                    callback=callback,
                )
            )
        return download_tasks
