from typing import NamedTuple


class BucketKeyMetadata(NamedTuple):
    """
    Storing meta-information about a bucket key.

    last_modified: ISO 8601 format

    bytes: file-size
    """

    last_modified: str
    bytes: int
