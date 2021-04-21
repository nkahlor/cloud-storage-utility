import logging
import time
import xmltodict

import ibm_boto3
from ibm_boto3.s3.transfer import TransferConfig
from ibm_botocore.config import Config
from ibm_botocore.exceptions import ClientError

from ..common.base_cloud_storage import BaseCloudStorage
from ..config import config


class IbmCloudStorage(BaseCloudStorage):
    """File operation implementations for IBM platform."""

    def __init__(self, session):
        super().__init__()
        self.__api_key = config.IBM_CONFIG["api_key"]
        self.__cos_crn = config.IBM_CONFIG["crn"]
        self.__auth_endpoint = config.IBM_CONFIG["auth_endpoint"]
        self.__cos_endpoint = config.IBM_CONFIG["cos_endpoint"]
        self.__session = session
        self.__expires_at = -1
        self.__access_token = ""

        self.__cos = self.__get_resource(
            self.__api_key, self.__cos_crn, self.__auth_endpoint, self.__cos_endpoint
        )

    async def get_bucket_keys(self, bucket_name, prefix=None, delimiter=None):
        try:
            access_token = await self.__get_auth_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            params = {"list-type": "2"}
            if prefix:
                params = {"prefix": prefix, **params}
            if delimiter:
                params = {"delimiter": delimiter, **params}

            all_items = {}
            is_truncated = True
            continuation_token = None
            while is_truncated:
                if continuation_token:
                    params = {"continuation-token": continuation_token}
                async with self.__session.get(
                    f"{self.__cos_endpoint}/{bucket_name}?list-type=2",
                    params=params,
                    headers=headers,
                ) as response:
                    xml_response = await response.text()
                    response_dict = xmltodict.parse(xml_response)["ListBucketResult"]
                    items = {
                        item["Key"]: {
                            "last_modified": item["LastModified"],
                            "bytes": item["Size"],
                        }
                        for item in response_dict["Contents"]
                    }

                    is_truncated = response_dict["IsTruncated"] == "true"
                    if is_truncated:
                        continuation_token = response_dict["NextContinuationToken"]
                    all_items.update(items)

        except Exception as error:
            logging.exception(error)
            return {}

        return all_items

    async def upload_file(self, bucket_name, cloud_key, file_path, callback=None):
        """
        Note: This should only be used for files < 500MB. When you need to upload larger files, you have to
        implement multi-part uploads.
        """
        upload_succeeded = None
        try:
            access_token = await self.__get_auth_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            with open(file_path, "rb") as file_data:
                async with self.__session.put(
                    f"{self.__cos_endpoint}/{bucket_name}/{cloud_key}",
                    data=file_data,
                    headers=headers,
                ):
                    pass
            upload_succeeded = True
        except Exception as error:
            logging.exception(error)
            upload_succeeded = False
        finally:
            if callback is not None:
                callback(
                    bucket_name=bucket_name,
                    cloud_key=cloud_key,
                    file_path=file_path,
                    succeeded=upload_succeeded,
                )
        return upload_succeeded

    async def remove_item(self, bucket_name, delete_request, callback=None):
        self.__cos.Bucket(bucket_name).delete_objects(Delete=delete_request)

        file_list = list(map(lambda x: x["Key"], delete_request["Objects"]))

        if callback is not None:
            callback(bucket_name, file_list, file_list)

    # Overriding the parent function because we can make it more efficient
    def get_remove_items_coroutines(self, bucket_name, item_names, callback=None):
        # do nothing
        if len(item_names) == 0:
            return []
        # the cloud function only allows up to 1000 keys per request, so we may
        # need many requests
        delete_requests = []
        delete_tasks = []
        try:
            request = []
            for i, name in enumerate(item_names):
                request.append({"Key": name})
                # every time the index is a mod of 1000, we know that's a
                # complete request
                if (i + 1) % 1000 == 0:
                    delete_requests.append({"Objects": request})
                    # reset request list for the next iteration
                    request = []
            # append whatever is left over
            if len(request) > 0:
                delete_requests.append({"Objects": request})

        except Exception as error:
            logging.exception(error)

        for request in delete_requests:
            delete_tasks.append(self.remove_item(bucket_name, request, callback))

        return delete_tasks

    async def download_file(
        self, bucket_name, cloud_key, destination_filepath, callback=None
    ):
        download_succeeded = None
        try:
            access_token = await self.__get_auth_token()
            headers = {"Authorization": f"Bearer {access_token}"}
            async with self.__session.get(
                f"{self.__cos_endpoint}/{bucket_name}/{cloud_key}",
                headers=headers,
            ) as response:
                with open(destination_filepath, "w") as downloaded_file:
                    downloaded_file.write(await response.text())

            download_succeeded = True
        except Exception as error:
            logging.exception(error)
            download_succeeded = False
        finally:
            if callback is not None:
                callback(
                    bucket_name=bucket_name,
                    cloud_key=cloud_key,
                    file_path=destination_filepath,
                    succeeded=download_succeeded,
                )

        return download_succeeded

    def __get_transfer_config(self, use_threads=True):
        # set the transfer threshold and chunk size
        return TransferConfig(
            use_threads=use_threads,
            multipart_threshold=self.file_threshold,
            multipart_chunksize=self.part_size,
        )

    @staticmethod
    def __get_resource(api_key, cos_crn, auth_endpoint, cos_endpoint):
        return ibm_boto3.resource(
            "s3",
            ibm_api_key_id=api_key,
            ibm_service_instance_id=cos_crn,
            ibm_auth_endpoint=auth_endpoint,
            config=Config(signature_version="oauth"),
            endpoint_url=cos_endpoint,
        )

    async def __get_auth_token(self):
        current_time = int(time.time())
        if current_time >= self.__expires_at:
            headers = {
                "content-type": "application/x-www-form-urlencoded",
                "accept": "application/json",
            }
            data = f"grant_type=urn%3Aibm%3Aparams%3Aoauth%3Agrant-type%3Aapikey&apikey={self.__api_key}"
            async with self.__session.post(
                self.__auth_endpoint, headers=headers, data=data
            ) as response:
                response = await response.json()
                self.__expires_at = response["expiration"]
                self.__access_token = response["access_token"]

        return self.__access_token
