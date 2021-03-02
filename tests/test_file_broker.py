import asyncio
from unittest.mock import patch

from cloud_storage_utility.config.config import DEFAULT_PLATFORM, SupportedPlatforms
from cloud_storage_utility.file_broker import FileBroker
from cloud_storage_utility.platforms.azure_cloud_storage import AzureCloudStorage
from cloud_storage_utility.platforms.ibm_cloud_storage import IbmCloudStorage


async def tmp_task():
    pass


class TestFileBroker:
    @staticmethod
    def get_loop_spy(mocker, event_loop):
        spy_loop = mocker.Mock(wraps=event_loop)
        mock_get_loop = mocker.patch.object(asyncio, "get_event_loop")
        mock_get_loop.return_value = spy_loop
        return spy_loop

    @staticmethod
    def assert_loop_invoked(spy_loop):
        spy_loop.run_until_complete.assert_called()
        spy_loop.close.assert_called()

    @patch.object(AzureCloudStorage, "_AzureCloudStorage__create_service_client")
    def test_broker_uses_correct_platform_when_specified(self, mock_azure):
        file_broker = FileBroker(platform=SupportedPlatforms.AZURE)

        assert file_broker.platform == SupportedPlatforms.AZURE
        assert isinstance(file_broker.service, AzureCloudStorage)

    def test_broker_uses_default_platform_when_not_specified(self):
        file_broker = FileBroker()

        assert file_broker.platform == DEFAULT_PLATFORM
        assert isinstance(file_broker.service, IbmCloudStorage)

    def test_upload_files_calls_service(self, event_loop, mocker):
        file_broker = FileBroker()
        file_broker.service.get_upload_files_coroutines = mocker.Mock(
            return_value=[tmp_task()]
        )
        spy_loop = self.get_loop_spy(mocker, event_loop)

        args = ("test", ["test"], None)
        file_broker.upload_files(*args)

        file_broker.service.get_upload_files_coroutines.assert_called_with(*args)
        self.assert_loop_invoked(spy_loop)

    def test_download_files_calls_service(self, event_loop, mocker):
        file_broker = FileBroker()
        file_broker.service.get_download_files_coroutines = mocker.Mock(
            return_value=[tmp_task()]
        )
        spy_loop = self.get_loop_spy(mocker, event_loop)

        args = ("test", "test", ["test"], None)
        file_broker.download_files(*args)

        file_broker.service.get_download_files_coroutines.assert_called_with(*args)
        self.assert_loop_invoked(spy_loop)

    def test_get_bucket_keys_calls_service(self, mocker):
        file_broker = FileBroker()
        file_broker.service.get_bucket_keys = mocker.Mock(return_value=["test_key"])

        args = "test"
        bucket_key_list = file_broker.get_bucket_keys(args)

        file_broker.service.get_bucket_keys.assert_called_with(args)
        assert len(bucket_key_list) > 0

    def test_remove_items_calls_service(self, event_loop, mocker):
        file_broker = FileBroker()
        file_broker.service.get_remove_items_coroutines = mocker.Mock(
            return_value=[tmp_task()]
        )
        spy_loop = self.get_loop_spy(mocker, event_loop)

        args = ("test", ["test"], None)
        file_broker.remove_items(*args)

        file_broker.service.get_remove_items_coroutines.assert_called_with(*args)
        self.assert_loop_invoked(spy_loop)
