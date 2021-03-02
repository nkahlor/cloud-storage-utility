import os

import abc
from concurrent.futures.thread import ThreadPoolExecutor


class BaseCloudStorage(metaclass=abc.ABCMeta):
    """
    Abstract definition of what a platform implementation needs to include. Any new platforms need to
    inherit from this.
    """
    def __init__(self):
        super().__init__()
        self.max_threads = 16
        # 5 MB chunks
        self.default_part_size = 1024 * 1024 * 5
        # 15 MB threshold
        self.default_file_threshold = 1024 * 1024 * 15

    @abc.abstractmethod
    def upload_files(self, bucket_name, cloud_map_list,
                     callback=None, args=None):
        """
        Upload a list of files from a local directory, and map them to they respective cloud keys
        in a particular bucket.

        :param bucket_name:
        :param cloud_map_list:
        :param args: Arguments for the callback
        :param callback: Executes every time a file is uploaded
        :type bucket_name: string
        :type cloud_map_list: list
        :return:
        """
        return

    @abc.abstractmethod
    def clear_bucket(self, bucket):
        """
        Clear everything out of the bucket.

        :param bucket:
        :type bucket: string
        :return:
        """
        return

    @abc.abstractmethod
    def remove_items(self, bucket_name, item_names):
        """
        Remove the specified keys from the bucket. Does not remove local files.

        :param bucket_name: Target bucket
        :param item_names: Keys to remove
        :type bucket_name: string
        :type item_names: list[string]
        :return: Keys deleted
        :rtype: list[string]
        """
        return

    @abc.abstractmethod
    def download_file(self, bucket_name, cloud_key,
                      destination_filepath, callback=None, args=None):
        """
        Download a single file from a bucket.

        :param bucket_name: Target bucket
        :param cloud_key: Key to download
        :param destination_filepath: Where to store the file
        :param callback: Function to execute after download finishes
        :param args: args for the callback
        :return:
        """
        return

    @abc.abstractmethod
    def get_bucket_keys(self, bucket_name):
        """
        List all keys (filenames) within a bucket.

        :param bucket_name: Target bucket
        :return:
        """
        return

    def download_files(self, local_directory, bucket_name,
                       cloud_key_list, callback=None, args=None):
        """
        Download all of the requested files from the bucket, and place them in the specified directory.

        :param callback: Executes after an individual file is downloaded
        :param args: args for the callback
        :param local_directory:
        :param bucket_name:
        :param cloud_key_list:
        :type local_directory: string
        :type bucket_name: string
        :type cloud_key_list: list[string]
        :return:
        """
        with ThreadPoolExecutor(self.max_threads) as executor:
            for name in cloud_key_list:
                base_name = os.path.basename(name)
                executor.submit(
                    self.download_file,
                    bucket_name,
                    name,
                    f"{local_directory}/{base_name}",
                    callback,
                    args)

    def sync_local_files(self, local_filename, bucket_name):
        """
        If a file in local storage is missing, grab it from the cloud storage.
        :param local_filename:
        :param bucket_name:
        :return:
        """
        if os.path.exists(local_filename):
            return True

        # This is the base filename and/or the "key" in the bucket
        cloud_key = os.path.basename(local_filename)
        return self.download_file(bucket_name, cloud_key, local_filename)
