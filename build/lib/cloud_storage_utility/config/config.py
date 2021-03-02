import os

from dotenv import load_dotenv

load_dotenv(dotenv_path="/Users/aa210665/Desktop/repo/cloud-storage-utility/.env")


class SupportedPlatforms:
    """ Lists all supported cloud platforms """
    AZURE = "azure"
    IBM = "ibm"


def __get_from_env(key):
    value = os.getenv(key)
    if value is None:
        print(f"{key} missing from environment")
    return value


DEFAULT_PLATFORM = SupportedPlatforms.IBM

IBM_CONFIG = {
    "api_key": __get_from_env("CSUTIL_IBM_API_KEY"),
    "auth_endpoint": __get_from_env("CSUTIL_IBM_AUTH_ENDPOINT"),
    "cos_endpoint": __get_from_env("CSUTIL_IBM_COS_ENDPOINT"),
    "crn": __get_from_env("CSUTIL_IBM_CRN")
}

AZURE_CONFIG = {
    "client_id": __get_from_env("CSUTIL_AZURE_CLIENT_ID"),
    "client_secret": __get_from_env("CSUTIL_AZURE_CLIENT_SECRET"),
    "storage_account_name": __get_from_env("CSUTIL_AZURE_STORAGE_ACCOUNT_NAME"),
    "tenant_id": __get_from_env("CSUTIL_AZURE_TENANT_ID")
}
