"""
Loads dotenv, if there is one.

Takes environment variables and puts them into dictionaries.
#### IBM
    | Environment Variable              | Config Dictionary           |
    |------------------------------     |-----------------------------|
    | IBMCLOUD_API_KEY (preferred)      | IBM_CONFIG['api_key']       |
    | CSUTIL_IBM_API_KEY                | IBM_CONFIG['api_key']       |
    | CSUTIL_IBM_AUTH_ENDPOINT          | IBM_CONFIG['auth_endpoint'] |
    | CSUTIL_IBM_COS_ENDPOINT           | IBM_CONFIG['cos_endpoint']  |
"""

import os

from dotenv import load_dotenv

from ..types.ibm_configuration import IbmConfiguration

load_dotenv()


class SupportedPlatforms:
    """Lists all supported cloud platforms"""

    IBM = "ibm"


def __get_from_env(key, backup=None):
    value = os.getenv(key)
    if backup and not value:
        return os.getenv(backup)
    return value


DEFAULT_PLATFORM = SupportedPlatforms.IBM

COS_CONFIG = {
    SupportedPlatforms.IBM: IbmConfiguration(
        auth_endpoint=__get_from_env("CSUTIL_IBM_AUTH_ENDPOINT"),
        cos_endpoint=__get_from_env("CSUTIL_IBM_COS_ENDPOINT"),
        api_key=__get_from_env("CSUTIL_IBM_API_KEY", backup="IBMCLOUD_API_KEY"),
    )
}
