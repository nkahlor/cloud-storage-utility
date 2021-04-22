"""
Loads dotenv, if there is one.

Takes environment variables and puts them into dictionaries.
#### IBM
    | Environment Variable     	| Config Dictionary           	|
    |--------------------------	|-----------------------------	|
    | CSUTIL_IBM_API_KEY       	| IBM_CONFIG['api_key']       	|
    | CSUTIL_IBM_AUTH_ENDPOINT 	| IBM_CONFIG['auth_endpoint'] 	|
    | CSUTIL_IBM_COS_ENDPOINT  	| IBM_CONFIG['cos_endpoint']  	|

#### Azure
    | Environment Variable              	| Config Dictionary                    	|
    |-----------------------------------	|--------------------------------------	|
    | CSUTIL_AZURE_CLIENT_ID            	| AZURE_CONFIG['client_id']            	|
    | CSUTIL_AZURE_CLIENT_SECRET        	| AZURE_CONFIG['client_secret']        	|
    | CSUTIL_AZURE_STORAGE_ACCOUNT_NAME 	| AZURE_CONFIG['storage_account_name'] 	|
    | CSUTIL_AZURE_TENANT_ID            	| AZURE_CONFIG['tenant_id']            	|
    | CSUTIL_AZURE_CONNECTION_STRING    	| AZURE_CONFIG['connection_string']    	|
"""

import os

from dotenv import load_dotenv

load_dotenv()


class SupportedPlatforms:
    """ Lists all supported cloud platforms """

    AZURE = "azure"
    IBM = "ibm"


def __get_from_env(key, backup=None):
    value = os.getenv(key)
    if backup and not value:
        return os.getenv(backup)
    return value


DEFAULT_PLATFORM = SupportedPlatforms.IBM

IBM_CONFIG = {
    "api_key": __get_from_env("CSUTIL_IBM_API_KEY", backup="IBMCLOUD_API_KEY"),
    "auth_endpoint": __get_from_env("CSUTIL_IBM_AUTH_ENDPOINT"),
    "cos_endpoint": __get_from_env("CSUTIL_IBM_COS_ENDPOINT"),
}

AZURE_CONFIG = {
    "client_id": __get_from_env("CSUTIL_AZURE_CLIENT_ID"),
    "client_secret": __get_from_env("CSUTIL_AZURE_CLIENT_SECRET"),
    "storage_account_name": __get_from_env("CSUTIL_AZURE_STORAGE_ACCOUNT_NAME"),
    "tenant_id": __get_from_env("CSUTIL_AZURE_TENANT_ID"),
    "connection_string": __get_from_env("CSUTIL_AZURE_CONNECTION_STRING"),
}
