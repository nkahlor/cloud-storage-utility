class CloudLocalMap:
    """Maps a local filepath to a remote cloud key"""

    def __init__(self, cloud_key: str, local_filepath: str):
        """Creates an association between a remote cloud key, and a local filepath.

        Args:
            cloud_key (str): The name of an item in a cloud bucket.
            local_filepath (str): The full path to a file on the local system.
        """
        self.cloud_key = cloud_key
        self.local_filepath = local_filepath
