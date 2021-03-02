import os

from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient

from ..common.base_cloud_storage import BaseCloudStorage
from ..config import config


class AzureCloudStorage(BaseCloudStorage):
    def __init__(self):
        super().__init__()
        self.service = self.__create_service_client()

    async def upload_file(self, bucket_name, local_filepath, callback=None, args=None):
        filesystem_client = self.service.get_file_system_client(file_system=bucket_name)
        cloud_file = os.path.basename(local_filepath)
        file_client = filesystem_client.get_file_client(cloud_file)
        file_client.create_file()

        with open(local_filepath, "rb") as file_handler:
            file_content = file_handler.read()
            # Append data to created file if it isn't empty
            if len(file_content) > 0:
                file_client.append_data(
                    file_content, offset=0, length=len(file_content)
                )
                file_client.flush_data(len(file_content))

        if callback is not None:
            callback(*args)

    async def remove_item(self, bucket_name, cloud_key, callback=None):
        filesystem_client = self.service.get_file_system_client(file_system=bucket_name)
        file_client = filesystem_client.get_file_client(cloud_key)
        file_client.delete_file()
        return cloud_key

    async def download_file(
        self, bucket_name, cloud_key, destination_filepath, callback=None, args=None
    ):
        base_file = os.path.basename(cloud_key)
        path = os.path.dirname(cloud_key)

        file_system_client = self.service.get_file_system_client(
            file_system=bucket_name
        )
        directory_client = file_system_client.get_directory_client(path)
        file_client = directory_client.get_file_client(base_file)

        download = file_client.download_file()
        downloaded_bytes = download.readall()

        local_file = open(destination_filepath, "wb")
        local_file.write(downloaded_bytes)
        local_file.close()

        if callback is not None:
            callback(*args)

    def get_bucket_keys(self, bucket_name):
        file_system = self.service.get_file_system_client(file_system=bucket_name)
        paths = file_system.get_paths()
        files = []
        for path in paths:
            files.append(path.name)

        return files

    @staticmethod
    def __create_service_client():
        # read the account information from the environment
        client_id = config.AZURE_CONFIG["client_id"]
        client_secret = config.AZURE_CONFIG["client_secret"]
        account_name = config.AZURE_CONFIG["storage_account_name"]
        tenant_id = config.AZURE_CONFIG["tenant_id"]
        connection_string = config.AZURE_CONFIG["connection_string"]

        # Prefer using a connection string if it's available
        if connection_string is not None:
            service_client = DataLakeServiceClient.from_connection_string(
                conn_str=connection_string
            )
        else:
            credential = ClientSecretCredential(tenant_id, client_id, client_secret)
            service_client = DataLakeServiceClient(
                account_url="{}://{}.dfs.core.windows.net".format(
                    "https", account_name
                ),
                credential=credential,
            )

        return service_client
