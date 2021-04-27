import aiohttp
import pytest
from aioresponses import aioresponses

from cloud_storage_utility.config.config import COS_CONFIG, SupportedPlatforms
from cloud_storage_utility.platforms.ibm_cloud_storage import IbmCloudStorage

config = COS_CONFIG[SupportedPlatforms.IBM]


class TestIbmCloudStorage:
    TEST_BUCKET = "test-bucket"
    TEST_FILE_PATH = "test_data/test_data_1.txt"
    NONEXISTENT_FILE = "test_data/nonexistent.txt"

    @pytest.mark.asyncio
    async def test_upload_file_succeeds(self, mocker):
        async with aiohttp.ClientSession() as session:
            ibm_service = IbmCloudStorage(session, config)

            mock_file = mocker.mock_open(read_data="test")
            mocker.patch(
                "cloud_storage_utility.platforms.ibm_cloud_storage.open", mock_file
            )

            with aioresponses() as mock_response:
                endpoint = f"{config.cos_endpoint}/test/test_data_1.txt"
                mock_response.put(endpoint, status=200)
                mock_response.post(
                    f"{config.auth_endpoint}",
                    payload={"access_token": "", "expiration": ""},
                )
                response = await ibm_service.upload_file(
                    "test", "test_data_1.txt", self.TEST_FILE_PATH
                )

            assert response is True

    @pytest.mark.asyncio
    async def test_upload_file_executes_its_callback_on_success(self, mocker):
        async with aiohttp.ClientSession() as session:
            ibm_service = IbmCloudStorage(session, config)
            mock_callback = mocker.Mock()

            mock_file = mocker.mock_open(read_data="test")
            mocker.patch(
                "cloud_storage_utility.platforms.ibm_cloud_storage.open", mock_file
            )

            with aioresponses() as mock_response:
                endpoint = f"{config.cos_endpoint}/test/test_data_1.txt"
                mock_response.put(endpoint, status=200)
                mock_response.post(
                    f"{config.auth_endpoint}",
                    payload={"access_token": "", "expiration": ""},
                )
                response = await ibm_service.upload_file(
                    "test",
                    "test_data_1.txt",
                    self.TEST_FILE_PATH,
                    callback=mock_callback,
                )

            assert response is True
            mock_callback.assert_called()

    @pytest.mark.asyncio
    async def test_upload_file_executes_callback_on_fail(self, mocker):
        async with aiohttp.ClientSession() as session:
            ibm_service = IbmCloudStorage(session, config)
            mock_callback = mocker.Mock()

            with aioresponses() as mock_response:
                endpoint = f"{config.cos_endpoint}/test/test_data_1.txt"
                mock_response.put(endpoint, status=404)
                mock_response.post(
                    f"{config.auth_endpoint}",
                    payload={"access_token": "", "expiration": ""},
                )
                response = await ibm_service.upload_file(
                    "test",
                    "test_data_1.txt",
                    self.TEST_FILE_PATH,
                    callback=mock_callback,
                )

            assert response is False
            mock_callback.assert_called()

    @pytest.mark.asyncio
    async def test_upload_file_fails_on_missing_local_file(self, mocker):
        async with aiohttp.ClientSession() as session:
            ibm_service = IbmCloudStorage(session, config)

            with aioresponses() as mock_response:
                endpoint = f"{config.cos_endpoint}/test/test_data_1.txt"
                mock_response.put(endpoint, status=200)
                mock_response.post(
                    f"{config.auth_endpoint}",
                    payload={"access_token": "", "expiration": ""},
                )
                response = await ibm_service.upload_file(
                    "test", "test_data_1.txt", self.TEST_FILE_PATH
                )

            assert response is False
