import logging
from ibm_botocore.exceptions import ClientError

import pytest

from cloud_storage_utility.platforms.ibm_cloud_storage import IbmCloudStorage


class TestIbmCloudStorage:
    TEST_BUCKET = "test-bucket"
    TEST_FILE_PATH = "test_data/test_data_1.txt"
    NONEXISTENT_FILE = "test_data/doesnt_exits.txt"

    def mock_boto_get_bucket_keys(self, mocker, expected_keys):
        class MockReturn:
            def __init__(self, key):
                self.key = key

        return_vals = [MockReturn(key) for key in expected_keys]

        # I apologize deeply for this fine Italian cuisine
        mock_all = mocker.Mock()
        mock_all.configure_mock(all=lambda: return_vals)
        mock_objects = mocker.Mock()
        mock_objects.configure_mock(objects=mock_all)
        mock_bucket = mocker.Mock(return_value=mock_objects)

        return mock_bucket

    def test_get_bucket_keys_succeeds(self, mocker):
        expected_keys = ["test.txt", "test2.txt"]

        ibm_service = IbmCloudStorage()

        mock_bucket = self.mock_boto_get_bucket_keys(mocker, expected_keys)

        ibm_service._IbmCloudStorage__cos.Bucket = mock_bucket  # type: ignore

        actual_keys = ibm_service.get_bucket_keys(self.TEST_BUCKET)

        assert expected_keys == actual_keys

    def test_get_bucket_keys_gives_empty_array_and_logs_when_fails(self, mocker):
        expected_keys = []

        mock_bucket = mocker.Mock(side_effect=Exception("not found"))
        mock_logger = mocker.patch.object(logging, "error")

        ibm_service = IbmCloudStorage()
        ibm_service._IbmCloudStorage__cos.Bucket = mock_bucket  # type: ignore

        actual_keys = ibm_service.get_bucket_keys(self.TEST_BUCKET)

        mock_logger.assert_called()
        assert expected_keys == actual_keys

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

    @pytest.mark.asyncio
    async def test_upload_file_fails_on_client_error(self, mocker):
        mock_object = mocker.Mock(
            side_effect=ClientError(error_response={"Error": {}}, operation_name="")
        )
        mock_logger = mocker.patch.object(logging, "error")

        mock_file = mocker.mock_open(read_data="test")
        mocker.patch(
            "cloud_storage_utility.platforms.ibm_cloud_storage.open", mock_file
        )

        service = IbmCloudStorage()
        service._IbmCloudStorage__cos.Object = mock_object  # type: ignore

        request_status = await service.upload_file(
            self.TEST_BUCKET, "test", self.TEST_FILE_PATH
        )

        mock_logger.assert_called()
        assert request_status is False

    @pytest.mark.asyncio
    async def test_upload_file_fails_on_generic_error(self, mocker):
        mock_object = mocker.Mock(side_effect=Exception("I'm generic"))
        mock_logger = mocker.patch.object(logging, "error")

        mock_file = mocker.mock_open(read_data="test")
        mocker.patch(
            "cloud_storage_utility.platforms.ibm_cloud_storage.open", mock_file
        )

        service = IbmCloudStorage()
        service._IbmCloudStorage__cos.Object = mock_object  # type: ignore

        request_status = await service.upload_file(
            self.TEST_BUCKET, "test", self.TEST_FILE_PATH
        )

        mock_logger.assert_called()
        assert request_status is False

    @pytest.mark.asyncio
    async def test_remove_item_succeeds(self, mocker):

        service = IbmCloudStorage()
        mock_delete_objects = mocker.Mock()
        mock_bucket = mocker.Mock(return_value=mock_delete_objects)
        service._IbmCloudStorage__cos.Bucket = mock_bucket  # type: ignore

        delete_requests = {"Objects": [{"Key": "test"}]}

        await service.remove_item(self.TEST_BUCKET, delete_requests)

        mock_bucket.assert_called_with(self.TEST_BUCKET)
        mock_delete_objects.delete_objects.assert_called_with(Delete=delete_requests)

    @pytest.mark.asyncio
    async def test_remove_file_executes_its_callback_on_success(self, mocker):

        service = IbmCloudStorage()

        mock_callback = mocker.Mock()
        mock_delete_objects = mocker.Mock()
        mock_bucket = mocker.Mock(return_value=mock_delete_objects)
        service._IbmCloudStorage__cos.Bucket = mock_bucket  # type: ignore

        delete_requests = {"Objects": [{"Key": "test"}]}

        await service.remove_item(self.TEST_BUCKET, delete_requests, mock_callback)

        mock_callback.assert_called()

    @pytest.mark.asyncio
    async def test_remove_file_executes_its_callback_on_failure(self, mocker):

        service = IbmCloudStorage()
        mock_logger = mocker.patch.object(logging, "error")

        mock_callback = mocker.Mock()
        mock_bucket = mocker.Mock(side_effect=Exception("Ahhhhh!"))
        service._IbmCloudStorage__cos.Bucket = mock_bucket  # type: ignore

        delete_requests = {"Objects": [{"Key": "test"}]}

        await service.remove_item(self.TEST_BUCKET, delete_requests, mock_callback)

        mock_callback.assert_called()
        mock_logger.assert_called()

    def test_get_remove_items_coroutines_returns_no_tasks_with_0_items(self, mocker):
        service = IbmCloudStorage()

        tasks = service.get_remove_items_coroutines(self.TEST_BUCKET, [])

        assert tasks == []

    def test_get_remove_items_coroutines_returns_correctly_for_2001_items(self, mocker):
        service = IbmCloudStorage()
        expected_num_tasks = 3

        items_to_remove = ["test.txt" for i in range(2001)]

        tasks = service.get_remove_items_coroutines(self.TEST_BUCKET, items_to_remove)

        assert expected_num_tasks == len(tasks)
        for task in tasks:
            assert task.__name__ == "remove_item"

    @pytest.mark.asyncio
    async def test_download_file_succeeds(self, mocker):
        ibm_service = IbmCloudStorage()

        mock_download_file = mocker.Mock()
        ibm_service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            return_value=mock_download_file
        )

        res = await ibm_service.download_file(
            self.TEST_BUCKET, "test.txt", "./test", None
        )

        mock_download_file.download_file.assert_called()
        assert res is True

    @pytest.mark.asyncio
    async def test_download_file_logs_error_on_failure(self, mocker):
        ibm_service = IbmCloudStorage()

        ibm_service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            side_effect=Exception("I failed :(")
        )

        res = await ibm_service.download_file(
            self.TEST_BUCKET, "test.txt", "./test", None
        )

        assert res is False

    @pytest.mark.asyncio
    async def test_download_file_executes_callback_on_success(self, mocker):
        ibm_service = IbmCloudStorage()

        mock_callback = mocker.Mock()
        mock_download_file = mocker.Mock()
        ibm_service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            return_value=mock_download_file
        )

        res = await ibm_service.download_file(
            self.TEST_BUCKET, "test.txt", "./test", mock_callback
        )

        mock_download_file.download_file.assert_called()
        assert res is True
        mock_callback.assert_called()

    @pytest.mark.asyncio
    async def test_download_file_executes_callback_on_failure(self, mocker):
        ibm_service = IbmCloudStorage()

        mock_callback = mocker.Mock()
        ibm_service._IbmCloudStorage__cos.Object = mocker.Mock(  # type: ignore
            side_effect=Exception("I failed :(")
        )

        res = await ibm_service.download_file(
            self.TEST_BUCKET, "test.txt", "./test", mock_callback
        )

        assert res is False
        mock_callback.assert_called()
