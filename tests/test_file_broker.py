import asyncio
from aioresponses import aioresponses
from unittest.mock import patch

import pytest

from cloud_storage_utility.config.config import DEFAULT_PLATFORM, SupportedPlatforms
from cloud_storage_utility.file_broker import FileBroker
from cloud_storage_utility.platforms.azure_cloud_storage import AzureCloudStorage
from cloud_storage_utility.platforms.ibm_cloud_storage import IbmCloudStorage

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


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
    async def test_broker_uses_correct_platform_when_specified(self, mock_azure):
        async with FileBroker(platform=SupportedPlatforms.AZURE) as file_broker:
            assert file_broker.platform == SupportedPlatforms.AZURE
            assert isinstance(file_broker.service, AzureCloudStorage)

    async def test_broker_uses_default_platform_when_not_specified(self):
        async with FileBroker() as file_broker:
            assert file_broker.platform == DEFAULT_PLATFORM
            assert isinstance(file_broker.service, IbmCloudStorage)

    async def test_upload_files_calls_service(self, mocker):
        async with FileBroker() as file_broker:
            file_broker.service.get_upload_files_coroutines = mocker.Mock(
                return_value=[tmp_task()]
            )

            args = ("test", ["test"], "", None)
            await file_broker.upload_files(*args)

            file_broker.service.get_upload_files_coroutines.assert_called_with(*args)

    async def test_download_files_calls_service(self, event_loop, mocker):
        async with FileBroker() as file_broker:
            file_broker.service.get_download_files_coroutines = mocker.Mock(
                return_value=[tmp_task()]
            )

            args = ("test", "test", ["test"], "", None)
            await file_broker.download_files(*args)

            file_broker.service.get_download_files_coroutines.assert_called_with(*args)

    async def test_get_bucket_keys_calls_service(self, mocker):
        async with FileBroker() as file_broker:
            result = asyncio.Future()
            result.set_result({"test.txt": {"bytes": 0, "last_modified": ""}})
            file_broker.service.get_bucket_keys = mocker.Mock(return_value=result)

            args = "test"
            bucket_key_list = await file_broker.get_bucket_keys(args)

            assert bucket_key_list == await result

    async def test_remove_items_calls_service(self, event_loop, mocker):
        async with FileBroker() as file_broker:
            file_broker.service.get_remove_items_coroutines = mocker.Mock(
                return_value=[tmp_task()]
            )

            args = ("test", ["test"], "", None)
            await file_broker.remove_items(*args)

            file_broker.service.get_remove_items_coroutines.assert_called_with(*args)
