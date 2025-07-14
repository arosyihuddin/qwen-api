import os
import mimetypes
import datetime as dt
import aiohttp
import requests
import asyncio
from oss2.utils import http_date
from oss2.utils import content_type_by_name
from oss2 import Auth, Bucket
from typing import AsyncGenerator, Generator, List, Optional, Union, Iterable
from ..core.types.upload_file import FileResult
from ..core.exceptions import QwenAPIError, RateLimitError
from ..core.types.chat import ChatResponseStream, ChatResponse, ChatMessage
from ..core.types.chat_model import ChatModel
from ..core.types.endpoint_api import EndpointAPI
from ..core.types.response.tool_param import ToolParam
from .tool_handle import (
    using_tools,
    action_selection,
    async_using_tools,
    async_action_selection,
)


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
        tools: Optional[Iterable[ToolParam]] = None,
    ) -> Union[ChatResponse, Generator[ChatResponseStream, None, None]]:
        use_tools = False
        if tools:
            use_tools = action_selection(
                messages, tools, model, temperature, max_tokens, stream, self._client
            )

        self._client.logger.debug(f"use tools: {use_tools}")

        if use_tools:
            tool_response = using_tools(
                messages, tools, model, temperature, max_tokens, stream, self._client
            )

            if stream:
                # Convert ChatResponse to a generator for streaming compatibility
                def tool_stream_generator():
                    from ..core.types.chat import ChoiceStream, Delta, Usage

                    # Create a streaming response from the tool response
                    delta = Delta(
                        role=tool_response.choices.message.role,
                        content=tool_response.choices.message.content,
                        function_call=None,
                        extra=tool_response.choices.extra,
                    )

                    choice_stream = ChoiceStream(delta=delta)

                    # Create a basic ChatMessage from the tool response
                    stream_message = ChatMessage(
                        role=tool_response.choices.message.role,
                        content=tool_response.choices.message.content or "",
                    )

                    # Create usage object (can be None for streaming)
                    usage = Usage()

                    stream_response = ChatResponseStream(
                        choices=[choice_stream], usage=usage, message=stream_message
                    )
                    yield stream_response

                return tool_stream_generator()
            else:
                return tool_response

        payload = self._client._build_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response = requests.post(
            url=self._client.base_url + EndpointAPI.completions,
            headers=self._client._build_headers(),
            json=payload,
            timeout=self._client.timeout,
            stream=stream,
        )

        if not response.ok:
            error_text = response.json()
            self._client.logger.error(f"API Error: {response.status_code} {error_text}")
            raise QwenAPIError(f"API Error: {response.status_code} {error_text}")

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
        tools: Optional[Iterable[ToolParam]] = None,
    ) -> Union[ChatResponse, AsyncGenerator[ChatResponseStream, None]]:
        session = None
        try:
            use_tools = False
            if tools:
                use_tools = await async_action_selection(
                    messages,
                    tools,
                    model,
                    temperature,
                    max_tokens,
                    stream,
                    self._client,
                )

            self._client.logger.debug(f"use tools: {use_tools}")

            if use_tools:
                tool_response = await async_using_tools(
                    messages,
                    tools,
                    model,
                    temperature,
                    max_tokens,
                    stream,
                    self._client,
                )

                if stream:
                    # Convert ChatResponse to an async generator for streaming compatibility
                    async def tool_astream_generator():
                        from ..core.types.chat import ChoiceStream, Delta, Usage

                        # Create a streaming response from the tool response
                        delta = Delta(
                            role=tool_response.choices.message.role,
                            content=tool_response.choices.message.content,
                            function_call=None,
                            extra=tool_response.choices.extra,
                        )

                        choice_stream = ChoiceStream(delta=delta)

                        # Create a basic ChatMessage from the tool response
                        stream_message = ChatMessage(
                            role=tool_response.choices.message.role,
                            content=tool_response.choices.message.content or "",
                        )

                        # Create usage object (can be None for streaming)
                        usage = Usage()

                        stream_response = ChatResponseStream(
                            choices=[choice_stream], usage=usage, message=stream_message
                        )
                        yield stream_response

                    return tool_astream_generator()
                else:
                    return tool_response

            payload = self._client._build_payload(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            session = aiohttp.ClientSession()
            # Track this session
            self._client._active_sessions.append(session)

            response = await session.post(
                url=self._client.base_url + EndpointAPI.completions,
                headers=self._client._build_headers(),
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self._client.timeout),
            )

            if not response.ok:
                error_text = await response.text()
                self._client.logger.error(f"API Error: {response.status} {error_text}")
                raise QwenAPIError(f"API Error: {response.status} {error_text}")

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
                # Remove from active sessions
                if session in self._client._active_sessions:
                    self._client._active_sessions.remove(session)
                await session.close()
            raise

    def upload_file(self, file_path: str = None, base64_data: str = None):
        if not file_path and not base64_data:
            raise QwenAPIError("Either file_path or base64_data must be provided")

        # If base64_data is provided, process it directly
        if base64_data:
            # Process base64 data
            import base64
            from io import BytesIO

            # Check if this is a data URI and extract the base64 part
            if base64_data.startswith("data:image/"):
                try:
                    header, data = base64_data.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                    is_base64 = True
                except QwenAPIError:
                    # Invalid data URI format, treat as regular base64 string
                    mime_type = "image/png"  # Default if we can't parse
                    data = base64_data
                    is_base64 = False
            else:
                data = base64_data
                mime_type = "image/png"
                is_base64 = True

            # Decode the base64 data
            try:
                file_content = base64.b64decode(data)
            except Exception as e:
                raise QwenAPIError(f"Invalid base64 data: {e}")

            # Create a temporary file name
            filename = "uploaded_image.png"
            if ";" in mime_type:
                mime_type = mime_type.split(";")[0]

            if "/" in mime_type:
                ext = mime_type.split("/")[-1].lower()
                if ext in ["jpeg", "jpg"]:
                    filename = f"uploaded_image.jpg"
                elif ext == "png":
                    filename = f"uploaded_image.png"
                elif ext == "gif":
                    filename = f"uploaded_image.gif"
                elif ext == "webp":
                    filename = f"uploaded_image.webp"

            # Get file size
            file_size = len(file_content)

        elif os.path.isfile(file_path):
            # Read file content
            with open(file_path, "rb") as file:
                file_content = file.read()

            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)

        else:
            raise QwenAPIError(f"File {file_path} does not exist")

        detected_mime_type = None
        if not base64_data:
            detected_mime_type, _ = mimetypes.guess_type(file_path)

        mime_type = detected_mime_type
        if base64_data:
            mime_type = mime_type or "image/png"

        payload = {
            "filename": filename,
            "filesize": file_size,
            "filetype": mime_type.split("/")[0] if mime_type else "image",
        }

        headers = self._client._build_headers()
        headers["Content-Type"] = "application/json"
        response = requests.post(
            url=self._client.base_url + EndpointAPI.upload_file,
            headers=headers,
            json=payload,
            timeout=self._client.timeout,
        )

        if not response.ok:
            try:
                error_text = response.json()
            except Exception:
                error_text = response.text()
            self._client.logger.error(f"API Error: {response.status_code} {error_text}")
            raise QwenAPIError(f"API Error: {response.status_code} {error_text}")

        if response.status_code == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        try:
            response_data = response.json()
        except Exception:
            response_data = response.text()

        # Extract credentials correctly
        access_key_id = response_data["access_key_id"]
        access_key_secret = response_data["access_key_secret"]
        region = response_data["region"]
        bucket_name = response_data.get("bucketname", "qwen-webui-prod")

        # Validate credentials
        if not access_key_id:
            raise QwenAPIError("AccessKey ID cannot be empty")
        if not access_key_secret:
            raise QwenAPIError("AccessKey Secret cannot be empty")

        # Get security token from response data
        security_token = response_data.get("security_token")
        if not security_token:
            raise QwenAPIError("Security token cannot be empty")

        # Create minimal required headers for signing
        request_datetime = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        # Use oss2 library to generate signed headers instead of manual signing
        endpoint = f"https://{region}.aliyuncs.com"
        auth = Auth(access_key_id, access_key_secret)
        bucket = Bucket(auth, endpoint, response_data["bucketname"])

        # Get current date in OSS format
        date_str = http_date()

        # Create basic headers
        oss_headers = {
            "Content-Type": (
                mime_type or content_type_by_name(file_path)
                if not base64_data
                else mime_type
            ),
            "Date": date_str,
            "x-oss-security-token": security_token,
            "x-oss-content-sha256": "UNSIGNED-PAYLOAD",
        }

        # Get current UTC time for signing
        request_datetime = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        oss_headers["date"] = request_datetime

        # Use the bucket's put_object method which handles signing automatically
        oss_response = bucket.put_object(
            key=response_data["file_path"], data=file_content, headers=oss_headers
        )

        # Add additional required headers for the OSS request
        oss_headers.update(
            {
                "x-oss-date": request_datetime,
                "Host": f"{bucket_name}.{region}.aliyuncs.com",
            }
        )

        # Check if the upload was successful
        if oss_response.status != 200 and oss_response.status != 203:
            error_text = oss_response.read()
            self._client.logger.error(f"API Error: {oss_response.status} {error_text}")
            raise QwenAPIError(f"API Error: {oss_response.status} {error_text}")

        if oss_response.status == 429:
            self._client.logger.error("Too many requests")
            raise RateLimitError("Too many requests")

        result = {
            "file_url": response_data["file_url"],
            "file_id": response_data["file_id"],
            "image_mimetype": mime_type,
        }
        return FileResult(**result)

    async def async_upload_file(self, file_path: str = None, base64_data: str = None):
        if not file_path and not base64_data:
            raise QwenAPIError("Either file_path or base64_data must be provided")

        # If base64_data is provided, process it directly
        if base64_data:
            # Process base64 data
            import base64
            from io import BytesIO

            # Check if this is a data URI and extract the base64 part
            if base64_data.startswith("data:image/"):
                try:
                    header, data = base64_data.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                    is_base64 = True
                except QwenAPIError:
                    # Invalid data URI format, treat as regular base64 string
                    mime_type = "image/png"  # Default if we can't parse
                    data = base64_data
                    is_base64 = False
            else:
                data = base64_data
                mime_type = "image/png"
                is_base64 = True

            # Decode the base64 data
            try:
                file_content = base64.b64decode(data)
            except Exception as e:
                raise QwenAPIError(f"Invalid base64 data: {e}")

            # Create a temporary file name
            filename = "uploaded_image.png"
            if ";" in mime_type:
                mime_type = mime_type.split(";")[0]

            if "/" in mime_type:
                ext = mime_type.split("/")[-1].lower()
                if ext in ["jpeg", "jpg"]:
                    filename = f"uploaded_image.jpg"
                elif ext == "png":
                    filename = f"uploaded_image.png"
                elif ext == "gif":
                    filename = f"uploaded_image.gif"
                elif ext == "webp":
                    filename = f"uploaded_image.webp"

            # Get file size
            file_size = len(file_content)

        elif os.path.isfile(file_path):
            # Read file content
            with open(file_path, "rb") as file:
                file_content = file.read()

            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)

        detected_mime_type = None
        if not base64_data:
            detected_mime_type, _ = mimetypes.guess_type(file_path)

        mime_type = detected_mime_type
        if base64_data:
            mime_type = mime_type or "image/png"

        payload = {
            "filename": filename,
            "filesize": file_size,
            "filetype": mime_type.split("/")[0] if mime_type else "image",
        }

        headers = self._client._build_headers()
        headers["Content-Type"] = "application/json"

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                url=self._client.base_url + EndpointAPI.upload_file,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self._client.timeout),
            )

            if not response.ok:
                error_text = response.json()
                self._client.logger.error(f"API Error: {response.status} {error_text}")
                raise QwenAPIError(f"API Error: {response.status} {error_text}")

            if response.status == 429:
                self._client.logger.error("Too many requests")
                raise RateLimitError("Too many requests")

            response_data = await response.json()

            # Extract credentials correctly
            access_key_id = response_data["access_key_id"]
            access_key_secret = response_data["access_key_secret"]
            region = response_data["region"]
            bucket_name = response_data.get("bucketname", "qwen-webui-prod")

            # Validate credentials
            if not access_key_id:
                raise QwenAPIError("AccessKey ID cannot be empty")
            if not access_key_secret:
                raise QwenAPIError("AccessKey Secret cannot be empty")

            # Get security token from response data
            security_token = response_data.get("security_token")
            if not security_token:
                raise QwenAPIError("Security token cannot be empty")

            # Create minimal required headers for signing
            request_datetime = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

            # Use oss2 library to generate signed headers instead of manual signing
            endpoint = f"https://{region}.aliyuncs.com"
            auth = Auth(access_key_id, access_key_secret)
            bucket = Bucket(auth, endpoint, response_data["bucketname"])

            # Get current date in OSS format
            date_str = http_date()

            # Create basic headers
            oss_headers = {
                "Content-Type": (
                    mime_type or content_type_by_name(file_path)
                    if not base64_data
                    else mime_type
                ),
                "Date": date_str,
                "x-oss-security-token": security_token,
                "x-oss-content-sha256": "UNSIGNED-PAYLOAD",
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
                        key=response_data["file_path"],
                        data=file_content if not base64_data else file_content,
                        headers=oss_headers,
                    ),
                )

                # Add additional required headers for the OSS request
                oss_headers.update(
                    {
                        "x-oss-date": request_datetime,
                        "Host": f"{bucket_name}.{region}.aliyuncs.com",
                    }
                )

                # Check if the upload was successful
                if oss_response.status != 200 and oss_response.status != 203:
                    error_text = oss_response.read()
                    self._client.logger.error(
                        f"API Error: {oss_response.status} {error_text}"
                    )
                    raise QwenAPIError(f"API Error: {oss_response.status} {error_text}")

                if oss_response.status == 429:
                    self._client.logger.error("Too many requests")
                    raise RateLimitError("Too many requests")

                result = {
                    "file_url": response_data["file_url"],
                    "file_id": response_data["file_id"],
                    "image_mimetype": mime_type,
                }
                return FileResult(**result)

            except Exception as e:
                self._client.logger.error(f"Error: {e}")
                raise
            finally:
                # Pastikan session ditutup
                self._client.logger.debug("Closing session")
