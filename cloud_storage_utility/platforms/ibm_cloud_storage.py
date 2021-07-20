import base64
import hashlib
import logging
import time
from typing import Dict

import xmltodict

from ..common.base_cloud_storage import BaseCloudStorage
from ..types.bucket_key import BucketKeyMetadata
from ..types.ibm_configuration import IbmConfiguration


class IbmCloudStorage(BaseCloudStorage):
    """File operation implementations for IBM platform."""

    def __init__(self, session, ibm_config: IbmConfiguration):
        super().__init__()
        self.__api_key = ibm_config.api_key
        self.__auth_endpoint = ibm_config.auth_endpoint
        self.__cos_endpoint = ibm_config.cos_endpoint
        self.__session = session
        self.__expires_at = -1
        self.__access_token = ""

    async def get_bucket_keys(
        self, bucket_name: str, prefix: str = ""
    ) -> Dict[str, BucketKeyMetadata]:
        try:
            access_token = await self.__get_auth_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            params: Dict[str, str] = {}
            if prefix and prefix != "":
                params = {"prefix": prefix.strip(), **params}

            all_items = {}
            is_truncated = True
            continuation_token = None
            while is_truncated:
                if continuation_token:
                    params = {
                        "continuation-token": continuation_token,
                        "prefix": prefix,
                    }
                async with self.__session.get(
                    f"{self.__cos_endpoint}/{bucket_name}?list-type=2",
                    params=params,
                    headers=headers,
                ) as response:
                    xml_response = await response.text()
                    response_dict = xmltodict.parse(xml_response)["ListBucketResult"]
                    if "Contents" in response_dict:
                        if "Key" in response_dict["Contents"]:
                            item = response_dict["Contents"]
                            items = {
                                item["Key"]:
                                    BucketKeyMetadata(
                                        last_modified=item["LastModified"],
                                        bytes=item["Size"],
                                    )

                            }
                        else:
                            items = {
                                item["Key"]:
                                    BucketKeyMetadata(
                                        last_modified=item["LastModified"],
                                        bytes=item["Size"],
                                    )
                                for item in response_dict["Contents"]
                            }

                        all_items.update(items)

                    is_truncated = response_dict["IsTruncated"] == "true"
                    if is_truncated:
                        continuation_token = response_dict["NextContinuationToken"]

        except Exception as error:
            logging.exception(error)
            return {}

        return dict(all_items)

    async def upload_file(
        self,
        bucket_name,
        cloud_key,
        file_path,
        prefix="",
        callback=None,
    ) -> bool:
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

            if prefix:
                cloud_key = f"{prefix}{cloud_key}"

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

    async def remove_item(self, bucket_name, delete_request, callback=None) -> bool:
        removal_succeeded = True
        try:
            xml_body = xmltodict.unparse({"Delete": delete_request})
            access_token = await self.__get_auth_token()
            md = hashlib.md5(xml_body.encode("utf-8")).digest()
            contents_md5 = base64.b64encode(md).decode("utf-8")
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-MD5": contents_md5,
                "Content-Type": "text/plain; charset=utf-8",
            }
            async with self.__session.post(
                f"{self.__cos_endpoint}/{bucket_name}?delete=",
                headers=headers,
                data=xml_body,
            ) as response:
                dict_response = xmltodict.parse(await response.text())["DeleteResult"][
                    "Deleted"
                ]
                # This is just dealing with a quirk in the xml parser, if only s3 used json like a normal person :(
                if "Key" in dict_response:
                    file_list = [dict_response["Key"]]
                else:
                    file_list = [elem["Key"] for elem in dict_response]
        except Exception as error:
            logging.exception(error)
            removal_succeeded = False
        finally:
            if callback is not None:
                callback(bucket_name, file_list)
        return removal_succeeded

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
                    delete_requests.append({"Object": request})
                    # reset request list for the next iteration
                    request = []
            # append whatever is left over
            if len(request) > 0:
                delete_requests.append({"Object": request})

        except Exception as error:
            logging.exception(error)

        for request in delete_requests:
            delete_tasks.append(self.remove_item(bucket_name, request, callback))

        return delete_tasks

    async def download_file(
        self,
        bucket_name,
        cloud_key,
        destination_filepath,
        prefix: str = "",
        callback=None,
    ) -> bool:
        download_succeeded = None
        try:
            access_token = await self.__get_auth_token()
            headers = {"Authorization": f"Bearer {access_token}"}
            async with self.__session.get(
                f"{self.__cos_endpoint}/{bucket_name}/{cloud_key}",
                headers=headers,
            ) as response:
                with open(destination_filepath, "wb") as downloaded_file:
                    downloaded_file.write(await response.read())

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
