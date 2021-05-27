from typing import NamedTuple


class IbmConfiguration(NamedTuple):
    auth_endpoint: str
    cos_endpoint: str
    api_key: str
    batch_limit: int = 1000
