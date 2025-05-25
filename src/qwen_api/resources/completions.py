import os
import mimetypes
import datetime as dt
import aiohttp
import requests
import aiofiles
import asyncio
from oss2.utils import http_date
from oss2.utils import content_type_by_name
from oss2 import Auth, Bucket
from typing import AsyncGenerator, Generator, List, Optional, Union
from ..core.types.upload_file import FileResult
from ..core.exceptions import QwenAPIError, RateLimitError
from ..core.types.chat import ChatResponseStream, ChatResponse, ChatMessage
from ..core.types.chat_model import ChatModel
from ..core.types.endpoint_api import EndpointAPI


class Completion:
    def __init__(self, client):
        self._client = client

    def create(
        self,
        messages: List[ChatMessage],
        model: ChatModel = "qwen-max-latest",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
    ) -> Union[ChatResponse, Generator[ChatResponseStream, None, None]]:
        payload = self._client._build_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        response = requests.post(
            url=self._client.base_url + EndpointAPI.completions,
            headers=self._client._build_headers(),
            json=payload,
            timeout=self._client.timeout,
            stream=stream
        )

        if not response.ok:
            error_text = response.json()
            self._client.logger.error(
                f"API Error: {response.status_code} {error_text}")
            raise QwenAPIError(
                f"API Error: {response.status_code} {error_text}")

        if response.status_code == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        self._client.logger.info(f"Response: {response.status_code}")

        if stream:
            return self._client._process_stream(response)
        try:
            return self._client._process_response(response)
        except Exception as e:
            self._client.logger.error(f"Error: {e}")

    async def acreate(
        self,
        messages: List[ChatMessage],
        model: ChatModel = "qwen-max-latest",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2048,
    ) -> Union[ChatResponse, AsyncGenerator[ChatResponseStream, None]]:
        session = None
        try:
            payload = self._client._build_payload(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            session = aiohttp.ClientSession()
            response = await session.post(
                url=self._client.base_url + EndpointAPI.completions,
                headers=self._client._build_headers(),
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            )

            if not response.ok:
                error_text = await response.text()
                self._client.logger.error(
                    f"API Error: {response.status} {error_text}")
                raise QwenAPIError(
                    f"API Error: {response.status} {error_text}")

            if response.status == 429:
                self._client.logger.error("Too many requests")
                raise RateLimitError("Too many requests")

            self._client.logger.info(f"Response status: {response.status}")

            if stream:
                return self._client._process_astream(response, session)
            try:
                return await self._client._process_aresponse(response, session)
            except Exception as e:
                self._client.logger.error(f"Error: {e}")

        except Exception as e:
            self._client.logger.error(f"Error in acreate: {e}")
            if session and not session.closed:
                await session.close()
            raise

    def upload_file(self, file_path: str, filesize: Optional[int] = None, filetype: Optional[str] = None):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = filesize or os.path.getsize(file_path)
        detected_mime_type = None
        if not filetype:
            detected_mime_type, _ = mimetypes.guess_type(file_path)

        mime_type = filetype or detected_mime_type or 'application/octet-stream'

        payload = {
            "filename": os.path.basename(file_path),
            "filesize": file_size,
            "filetype": mime_type.split('/')[0] if mime_type else "application"
        }

        headers = self._client._build_headers()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            url=self._client.base_url + EndpointAPI.upload_file,
            headers=headers,
            json=payload,
            timeout=self._client.timeout
        )

        if not response.ok:
            try:
                error_text = response.json()
            except Exception:
                error_text = response.text()
            self._client.logger.error(
                f"API Error: {response.status} {error_text}")
            raise QwenAPIError(
                f"API Error: {response.status} {error_text}")

        if response.status == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        try:
            response_data = response.json()
        except Exception:
            response_data = response.text()

        # Extract credentials correctly
        access_key_id = response_data['access_key_id']
        access_key_secret = response_data['access_key_secret']
        region = response_data['region']
        bucket_name = response_data.get('bucketname', 'qwen-webui-prod')

        # Validate credentials
        if not access_key_id:
            raise ValueError("AccessKey ID cannot be empty")
        if not access_key_secret:
            raise ValueError("AccessKey Secret cannot be empty")

        # Get security token from response data
        security_token = response_data.get('security_token')
        if not security_token:
            raise ValueError("Security token cannot be empty")

        # Create minimal required headers for signing
        request_datetime = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        # Read file content
        with open(file_path, 'rb') as file:
            file_content = file.read()

        # Use oss2 library to generate signed headers instead of manual signing

        endpoint = f"https://{region}.aliyuncs.com"
        auth = Auth(access_key_id, access_key_secret)
        bucket = Bucket(auth, endpoint, response_data['bucketname'])

        # Get current date in OSS format
        date_str = http_date()

        # Create basic headers
        oss_headers = {
            'Content-Type': mime_type or content_type_by_name(file_path),
            'Date': date_str,
            'x-oss-security-token': security_token,
            'x-oss-content-sha256': 'UNSIGNED-PAYLOAD'
        }

        # Get current UTC time for signing
        request_datetime = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        oss_headers["date"] = request_datetime

        # Use the bucket's put_object method which handles signing automatically
        oss_response = bucket.put_object(
            key=response_data['file_path'],
            data=file_content,
            headers=oss_headers
        )

        # Add additional required headers for the OSS request
        oss_headers.update({
            "x-oss-date": request_datetime,
            "Host": f"{bucket_name}.{region}.aliyuncs.com"
        })

        # Check if the upload was successful
        if oss_response.status != 200 and oss_response.status != 203:
            error_text = oss_response.read()
            self._client.logger.error(
                f"API Error: {oss_response.status} {error_text}")
            raise QwenAPIError(
                f"API Error: {oss_response.status} {error_text}")

        if oss_response.status == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        result = {
            "file_url": response_data['file_url'],
            "file_id": response_data['file_id'],
            "image_mimetype": mime_type
        }
        return FileResult(**result)

    async def async_upload_file(self, file_path: str, filesize: Optional[int] = None, filetype: Optional[str] = None):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = filesize or os.path.getsize(file_path)
        detected_mime_type = None
        if not filetype:
            detected_mime_type, _ = mimetypes.guess_type(file_path)

        mime_type = filetype or detected_mime_type or 'application/octet-stream'

        payload = {
            "filename": os.path.basename(file_path),
            "filesize": file_size,
            "filetype": mime_type.split('/')[0] if mime_type else "application"
        }

        headers = self._client._build_headers()
        headers['Content-Type'] = 'application/json'

        # Ganti dengan async request
        # session = aiohttp.ClientSession()
        # response = await session.post(
        #     url=self._client.base_url + EndpointAPI.upload_file,
        #     headers=headers,
        #     json=payload,
        #     timeout=aiohttp.ClientTimeout(total=120)
        # )
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=self._client.base_url + EndpointAPI.upload_file,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            )

            if not response.ok:
                error_text = response.json()
                self._client.logger.error(
                    f"API Error: {response.status_code} {error_text}")
                raise QwenAPIError(
                    f"API Error: {response.status_code} {error_text}")

            if response.status == 429:
                self._client.logger.error("Too many requests")
                raise RateLimitError("Too many requests")

            response_data = await response.json()

            # Extract credentials correctly
            access_key_id = response_data['access_key_id']
            access_key_secret = response_data['access_key_secret']
            region = response_data['region']
            bucket_name = response_data.get('bucketname', 'qwen-webui-prod')

            # Validate credentials
            if not access_key_id:
                raise ValueError("AccessKey ID cannot be empty")
            if not access_key_secret:
                raise ValueError("AccessKey Secret cannot be empty")

            # Get security token from response data
            security_token = response_data.get('security_token')
            if not security_token:
                raise ValueError("Security token cannot be empty")

            # Create minimal required headers for signing
            request_datetime = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

            # Read file content asynchronously
            async with aiofiles.open(file_path, 'rb') as file:
                file_content = await file.read()

            # Use oss2 library to generate signed headers instead of manual signing

            endpoint = f"https://{region}.aliyuncs.com"
            auth = Auth(access_key_id, access_key_secret)
            bucket = Bucket(auth, endpoint, response_data['bucketname'])

            # Get current date in OSS format
            date_str = http_date()

            # Create basic headers
            oss_headers = {
                'Content-Type': mime_type or content_type_by_name(file_path),
                'Date': date_str,
                'x-oss-security-token': security_token,
                'x-oss-content-sha256': 'UNSIGNED-PAYLOAD'
            }

            # Get current UTC time for signing
            request_datetime = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            oss_headers["date"] = request_datetime

            # Use an async executor to run the synchronous oss2 operations
            loop = asyncio.get_event_loop()
            # session = aiohttp.ClientSession()

            try:
                # Use the bucket's put_object method which handles signing automatically
                oss_response = await loop.run_in_executor(
                    None,
                    lambda: bucket.put_object(
                        key=response_data['file_path'],
                        data=file_content,
                        headers=oss_headers
                    )
                )

                # Add additional required headers for the OSS request
                oss_headers.update({
                    "x-oss-date": request_datetime,
                    "Host": f"{bucket_name}.{region}.aliyuncs.com"
                })

                # Check if the upload was successful
                if oss_response.status != 200 and oss_response.status != 203:
                    error_text = oss_response.read()
                    self._client.logger.error(
                        f"API Error: {oss_response.status} {error_text}")
                    raise QwenAPIError(
                        f"API Error: {oss_response.status} {error_text}")

                if oss_response.status == 429:
                    self._client.logger.error("Too many requests")
                    raise RateLimitError("Too many requests")

                result = {
                    "file_url": response_data['file_url'],
                    "file_id": response_data['file_id'],
                    "image_mimetype": mime_type
                }
                return FileResult(**result)

            except Exception as e:
                self._client.logger.error(f"Error: {e}")
                raise
            finally:
                # Pastikan session ditutup
                self._client.logger.debug("Closing session")
