class CloudLocalMap:
    """ Maps a local filepath to a remote cloud key """
    def __init__(self, cloud_key, local_filepath):
        self.cloud_key = cloud_key
        self.local_filepath = local_filepath
