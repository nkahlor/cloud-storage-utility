import logging

import pytest

from cloud_storage_utility.platforms.ibm_cloud_storage import IbmCloudStorage


class TestIbmCloudStorage:
    TEST_BUCKET = "test-bucket"
    TEST_FILE_PATH = "test_data/test_data_1.txt"
    NONEXISTENT_FILE = "test_data/doesnt_exits.txt"

    @pytest.mark.asyncio
    async def test_upload_file_succeeds(self, mocker):
        ibm_service = IbmCloudStorage()

        mock_file = mocker.mock_open(read_data="test")
        mocker.patch(
            "cloud_storage_utility.platforms.ibm_cloud_storage.open", mock_file
        )

        mock_upload_fileobj = mocker.Mock()
        ibm_service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            return_value=mock_upload_fileobj
        )

        res = await ibm_service.upload_file(
            self.TEST_BUCKET, "test", self.TEST_FILE_PATH, None
        )

        mock_upload_fileobj.upload_fileobj.assert_called()
        assert res is True

    @pytest.mark.asyncio
    async def test_upload_file_executes_its_callback_on_success(self, mocker):

        service = IbmCloudStorage()

        mock_callback = mocker.Mock()
        mock_file = mocker.mock_open(read_data="test")
        mocker.patch(
            "cloud_storage_utility.platforms.ibm_cloud_storage.open", mock_file
        )
        mock_upload_fileobj = mocker.Mock()
        service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            return_value=mock_upload_fileobj
        )

        await service.upload_file(
            self.TEST_BUCKET, "test", self.TEST_FILE_PATH, mock_callback
        )

        mock_callback.assert_called()

    @pytest.mark.asyncio
    async def test_upload_file_executes_callback_on_fail(self, mocker):
        # Forcing it to throw a file not found error

        service = IbmCloudStorage()

        mock_callback = mocker.Mock()
        mock_upload_file = mocker.Mock()
        service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            return_value=mock_upload_file
        )

        await service.upload_file(
            self.TEST_BUCKET, "test", self.NONEXISTENT_FILE, mock_callback
        )

        mock_callback.assert_called()

    @pytest.mark.asyncio
    async def test_upload_file_skips_callback_when_not_defined(self, mocker):
        service = IbmCloudStorage()

        mock_callback = mocker.Mock()
        mock_file = mocker.mock_open(read_data="test")
        mocker.patch(
            "cloud_storage_utility.platforms.ibm_cloud_storage.open", mock_file
        )
        mock_upload_fileobj = mocker.Mock()
        service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            return_value=mock_upload_fileobj
        )

        await service.upload_file(self.TEST_BUCKET, "test", self.NONEXISTENT_FILE, None)

        mock_callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_file_fails_on_missing_local_file(self, mocker):

        service = IbmCloudStorage()

        mock_logger = mocker.patch.object(logging, "error")
        mock_upload_fileobj = mocker.Mock()
        service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            return_value=mock_upload_fileobj
        )

        request_status = await service.upload_file(
            self.TEST_BUCKET, "test", self.NONEXISTENT_FILE
        )

        assert request_status is False
        mock_logger.assert_called()
