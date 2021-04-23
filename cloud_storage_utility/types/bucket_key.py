from typing import NamedTuple


class BucketKeyMetadata(NamedTuple):
    """
    Storing meta-information about a bucket key.

    last_modified: unix timestamp

    bytes: file-size
    """

    last_modified: int
    bytes: str
