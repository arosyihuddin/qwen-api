import json
from typing import AsyncGenerator, Generator, List, Optional, Union
import requests
import aiohttp
from sseclient import SSEClient
from pydantic import ValidationError
from .core.auth_manager import AuthManager
from .logger import setup_logger
from .core.types.chat import (
    ChatResponse,
    ChatResponseStream,
    ChatMessage,
    MessageRole,
    ChoiceStream,
    Extra,
    Delta,
    Usage,
)
from .resources.completions import Completion
from .utils.promp_system import WEB_DEVELOPMENT_PROMPT
from .core.exceptions import QwenAPIError
from .core.types.response.function_tool import ToolCall, Function


class Qwen:
    def __init__(
        self,
        api_key: Optional[str] = None,
        cookie: Optional[str] = None,
        base_url: str = "https://chat.qwen.ai",
        timeout: int = 600,
        log_level: str = "INFO",
        save_logs: bool = False,
    ):
        self.chat = Completion(self)
        self.timeout = timeout
        self.auth = AuthManager(token=api_key, cookie=cookie)
        self.logger = setup_logger(log_level=log_level, save_logs=save_logs)
        self.base_url = base_url
        self._active_sessions = []
        self._is_cancelled = False

    def _build_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": self.auth.get_token(),
            "Cookie": self.auth.get_cookie(),
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "Host": "chat.qwen.ai",
            "Origin": "https://chat.qwen.ai",
        }

    def _build_payload(
        self,
        messages: List[ChatMessage],
        temperature: float,
        model: str,
        max_tokens: Optional[int],
    ) -> dict:
        validated_messages = []

        for msg in messages:
            if isinstance(msg, dict):
                try:
                    validated_msg = ChatMessage(**msg)
                except ValidationError as e:
                    raise QwenAPIError(f"Error validating message: {e}")
            else:
                validated_msg = msg

            if validated_msg.role == "system":
                if (
                    validated_msg.web_development
                    and WEB_DEVELOPMENT_PROMPT not in validated_msg.content
                ):
                    updated_content = (
                        f"{validated_msg.content}\n\n{WEB_DEVELOPMENT_PROMPT}"
                    )
                    validated_msg = ChatMessage(
                        **{**validated_msg.model_dump(), "content": updated_content}
                    )

            validated_messages.append(
                {
                    "role": (
                        MessageRole.FUNCTION
                        if validated_msg.role == MessageRole.TOOL
                        else (
                            validated_msg.role
                            if validated_msg.role == MessageRole.SYSTEM
                            else MessageRole.USER
                        )
                    ),
                    "content": (
                        validated_msg.blocks[0].text
                        if len(validated_msg.blocks) == 1
                        and validated_msg.blocks[0].block_type == "text"
                        else [
                            (
                                {"type": "text", "text": block.text}
                                if block.block_type == "text"
                                else (
                                    {"type": "image", "image": str(block.url)}
                                    if block.block_type == "image"
                                    else {"type": block.block_type}
                                )
                            )
                            for block in validated_msg.blocks
                        ]
                    ),
                    "chat_type": (
                        "artifacts"
                        if getattr(validated_msg, "web_development", False)
                        else (
                            "search"
                            if getattr(validated_msg, "web_search", False)
                            else "t2t"
                        )
                    ),
                    "feature_config": {
                        "thinking_enabled": getattr(validated_msg, "thinking", False),
                        "thinking_budget": getattr(validated_msg, "thinking_budget", 0),
                        "output_schema": getattr(validated_msg, "output_schema", None),
                    },
                    "extra": {},
                }
            )

        return {
            "stream": True,
            "model": model,
            "incremental_output": True,
            "messages": validated_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _process_response(self, response: requests.Response) -> ChatResponse:
        from .core.types.chat import Choice, Message, Extra

        client = SSEClient(response)
        extra = None
        text = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data["choices"][0]["delta"].get("role") == "function":
                        extra_data = data["choices"][0]["delta"].get("extra")
                        if extra_data:
                            extra = Extra(**extra_data)
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        message = Message(role="assistant", content=text)
        choice = Choice(message=message, extra=extra)
        return ChatResponse(choices=choice)

    def _process_response_tool(
        self, response: requests.Response
    ) -> ChatResponse | QwenAPIError:
        from .core.types.chat import Choice, Message, Extra

        client = SSEClient(response)
        extra = None
        text = ""
        for event in client.events():
            if event.data:
                try:
                    data = json.loads(event.data)
                    if data["choices"][0]["delta"].get("role") == "function":
                        extra_data = data["choices"][0]["delta"].get("extra")
                        if extra_data:
                            extra = Extra(**extra_data)
                    text += data["choices"][0]["delta"].get("content")
                except json.JSONDecodeError:
                    continue
        try:
            self.logger.debug(f"text: {text}")
            parse_json = json.loads(text)
            if isinstance(parse_json["arguments"], str):
                parse_arguments = json.loads(parse_json["arguments"])
            else:
                parse_arguments = parse_json["arguments"]
            self.logger.debug(f"parse_json: {parse_json}")
            self.logger.debug(f"arguments: {parse_arguments}")
            function = Function(name=parse_json["name"], arguments=parse_arguments)
            message = Message(
                role="assistant", content="", tool_calls=[ToolCall(function=function)]
            )
            choice = Choice(message=message, extra=extra)
            return ChatResponse(choices=choice)
        except json.JSONDecodeError as e:
            return QwenAPIError(f"Error decoding JSON response: {e}")

    async def _process_aresponse(
        self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> ChatResponse:
        from .core.types.chat import Choice, Message, Extra

        # Track this session
        self._active_sessions.append(session)

        try:
            extra = None
            text = ""
            async for line in response.content:
                # Check if cancelled
                if self._is_cancelled:
                    self.logger.info("Async response processing cancelled")
                    break

                if line.startswith(b"data:"):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            extra_data = data["choices"][0]["delta"].get("extra")
                            if extra_data:
                                extra = Extra(**extra_data)
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            message = Message(role="assistant", content=text)
            choice = Choice(message=message, extra=extra)
            return ChatResponse(choices=choice)
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            raise

        finally:
            # Remove from active sessions
            if session in self._active_sessions:
                self._active_sessions.remove(session)
            await session.close()

    # async def _process_aresponse_tool_stream(
    #     self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    # ) -> AsyncGenerator[Union[ChatResponseStream, QwenAPIError], None]:
    #     """
    #     Memproses response stream dan menghasilkan ChatResponseStream untuk teks dan tool call.
    #     """
    #
    #     self._active_sessions.append(session)
    #
    #     # --- State untuk akumulasi dan deteksi ---
    #     self.accumulated_content = ""  # Buffer untuk mengakumulasi semua konten
    #     self.is_potential_tool_call = False  # Flag jika buffer mungkin berisi tool call
    #     self.is_inside_json_object = False  # Flag jika sedang mengakumulasi objek JSON
    #     self.brace_count = 0  # Menghitung keseimbangan { }
    #     self.potential_tool_call_buffer = (
    #         ""  # Buffer khusus untuk konten yang dianggap tool call
    #     )
    #     tool_call_extra: Optional[Extra] = None  # Untuk menyimpan extra jika ada
    #
    #     try:
    #         async for line in response.content:
    #             if self._is_cancelled:
    #                 self.logger.info("Async tool response processing cancelled")
    #                 break
    #
    #             if line.startswith(b"data:"):
    #                 try:
    #                     data = json.loads(line[5:].decode())
    #                     delta_data = data["choices"][0]["delta"]
    #
    #                     content_delta = delta_data.get("content", "")
    #
    #                     if not content_delta:
    #                         # Tidak ada konten, mungkin hanya delta.role atau delta.extra
    #                         # Jika ada extra, simpan
    #                         extra_data = delta_data.get("extra")
    #                         if extra_data:
    #                             # Asumsikan Extra bisa dibuat dari dict
    #                             tool_call_extra = (
    #                                 Extra(**extra_data)
    #                                 if isinstance(extra_data, dict)
    #                                 else Extra()
    #                             )
    #                         continue
    #
    #                     # --- Akumulasi konten ---
    #                     self.accumulated_content += content_delta
    #
    #                     # --- Deteksi awal potensi tool call ---
    #                     # Heuristik sederhana: jika 100 karakter pertama (setelah strip)
    #                     # dimulai dengan '{' dan mengandung '"name"', tandai sebagai potensi tool call.
    #                     # Ini bisa menghasilkan positif palsu, jadi perlu validasi lebih lanjut.
    #                     if (
    #                         not self.is_potential_tool_call
    #                         and len(self.accumulated_content) > 10
    #                     ):
    #                         stripped_start = self.accumulated_content.strip()
    #                         print(stripped_start)
    #                         if (
    #                             stripped_start.startswith("{")
    #                             and '"name"'
    #                             in stripped_start[: min(100, len(stripped_start))]
    #                         ):
    #                             self.is_potential_tool_call = True
    #                             self.logger.debug(
    #                                 "Potential tool call detected based on prefix."
    #                             )
    #
    #                     # --- Jika terdeteksi sebagai potensi tool call, proses lebih lanjut ---
    #                     if self.is_potential_tool_call:
    #                         # Tambahkan delta ke buffer khusus tool call
    #                         self.potential_tool_call_buffer += content_delta
    #
    #                         # Hitung brace untuk mendeteksi akhir objek JSON
    #                         for char in content_delta:
    #                             if char == "{":
    #                                 self.brace_count += 1
    #                                 self.is_inside_json_object = True
    #                             elif char == "}":
    #                                 self.brace_count -= 1
    #                                 # Jika brace seimbang dan kita sedang dalam objek, mungkin JSON selesai
    #                                 if (
    #                                     self.brace_count == 0
    #                                     and self.is_inside_json_object
    #                                 ):
    #                                     # --- Coba parse buffer tool call ---
    #                                     try:
    #                                         parse_json = json.loads(
    #                                             self.potential_tool_call_buffer.strip()
    #                                         )
    #                                         # Validasi dasar
    #                                         if (
    #                                             isinstance(parse_json, dict)
    #                                             and "name" in parse_json
    #                                             and "arguments" in parse_json
    #                                         ):
    #                                             self.logger.info(
    #                                                 f"Valid tool call JSON detected and parsed: {parse_json.get('name', 'Unknown')}"
    #                                             )
    #                                             # Buat dan yield ChatResponseStream untuk tool call
    #                                             yield await self._create_tool_call_response(
    #                                                 parse_json, tool_call_extra
    #                                             )
    #
    #                                             # Reset state untuk tool call berikutnya
    #                                             self.is_potential_tool_call = False
    #                                             self.is_inside_json_object = False
    #                                             self.brace_count = 0
    #                                             self.potential_tool_call_buffer = ""
    #                                             tool_call_extra = None  # Reset extra setelah digunakan
    #                                             # Jangan yield content_delta lagi karena sudah diproses sebagai tool call
    #                                             content_delta = ""  # Kosongkan agar tidak diyield sebagai teks
    #                                             break  # Keluar dari loop karakter
    #                                         else:
    #                                             # Bukan tool call yang valid, mungkin JSON parsial atau salah format
    #                                             # Bisa log warning
    #                                             self.logger.debug(
    #                                                 "Accumulated buffer is not a valid tool call JSON structure."
    #                                             )
    #                                     except json.JSONDecodeError:
    #                                         # Masih belum lengkap atau ada error, lanjut akumulasi
    #                                         # self.logger.debug("JSONDecodeError while parsing potential tool call buffer, continuing accumulation.")
    #                                         pass  # Terus akumulasi
    #
    #                     # --- Yield teks biasa jika ada content_delta yang tersisa ---
    #                     # (Ini akan kosong jika content_delta sudah diproses sebagai tool call)
    #                     if content_delta:
    #                         delta = Delta(role="assistant", content=content_delta)
    #                         choice_stream = ChoiceStream(delta=delta)
    #                         stream_message = ChatMessage(
    #                             role="assistant", content=content_delta
    #                         )
    #                         stream_response = ChatResponseStream(
    #                             choices=[choice_stream],
    #                             usage=Usage(),
    #                             message=stream_message,
    #                         )
    #                         yield stream_response
    #
    #                 except json.JSONDecodeError:
    #                     self.logger.warning(f"Failed to decode JSON line: {line}")
    #                     continue
    #
    #         # --- Di akhir stream, cek jika ada sisa konten yang bukan tool call ---
    #         # Ini menangani kasus teks penjelasan yang muncul setelah tool call
    #         if self.accumulated_content and not self.is_potential_tool_call:
    #             # Ada konten yang terakumulasi tapi tidak terdeteksi sebagai tool call
    #             # Anggap sebagai teks biasa dan yield
    #             # Namun, kita perlu hati-hati karena accumulated_content mungkin mencakup
    #             # teks sebelum tool call juga.
    #             # Untuk kesederhanaan, kita yield seluruh accumulated_content jika
    #             # bukan bagian dari tool call yang sedang diakumulasi.
    #             # Ini bisa menyebabkan duplikasi jika logika sebelumnya tidak sempurna.
    #             # Logika yang lebih baik akan memisahkan teks yang sudah diyield.
    #             # Untuk sekarang, kita asumsikan teks yang diyield sebelumnya tidak tumpang tindih.
    #             remaining_text = self.accumulated_content.strip()
    #             if remaining_text:
    #                 delta = Delta(role="assistant", content=remaining_text)
    #                 choice_stream = ChoiceStream(delta=delta)
    #                 stream_message = ChatMessage(
    #                     role="assistant", content=remaining_text
    #                 )
    #                 stream_response = ChatResponseStream(
    #                     choices=[choice_stream], usage=Usage(), message=stream_message
    #                 )
    #                 yield stream_response
    #
    #     except aiohttp.ClientError as e:
    #         self.logger.error(f"Client error during streaming: {e}")
    #         yield QwenAPIError(f"Client error: {e}")
    #     finally:
    #         # Bersihkan state
    #         self.accumulated_content = ""
    #         self.is_potential_tool_call = False
    #         self.is_inside_json_object = False
    #         self.brace_count = 0
    #         self.potential_tool_call_buffer = ""
    #         tool_call_extra = None
    #
    #         if session in self._active_sessions:
    #             self._active_sessions.remove(session)
    #         await session.close()
    #
    # async def _create_tool_call_response(
    #     self, parse_json: dict, tool_call_extra: Optional[Extra]
    # ) -> ChatResponseStream:
    #     """Membuat objek ChatResponseStream untuk tool call yang telah di-parsing."""
    #
    #     if (
    #         not isinstance(parse_json, dict)
    #         or "name" not in parse_json
    #         or "arguments" not in parse_json
    #     ):
    #         error_msg = f"Invalid tool call format received: {parse_json}"
    #         self.logger.error(error_msg)
    #         # Return QwenAPIError sebagai ChatResponseStream? Atau raise?
    #         # Untuk konsistensi streaming, kita buat objek error khusus streaming jika ada
    #         # atau kembalikan sebagai error dalam stream.
    #         # Misalnya, buat ChoiceStream khusus error.
    #         # Untuk sekarang, kita asumsikan QwenAPIError bisa di-yield.
    #         # Tapi ini mungkin perlu penyesuaian.
    #         # Mari kita kembalikan sebagai error biasa untuk sekarang.
    #         return QwenAPIError(error_msg)  # Ini akan di-yield oleh fungsi pemanggil
    #
    #     arguments = parse_json["arguments"]
    #     if isinstance(arguments, str):
    #         arguments = json.loads(
    #             arguments
    #         )  # Jika argumen adalah string JSON, parse lagi
    #
    #     function = Function(name=parse_json["name"], arguments=arguments)
    #     tool_call = ToolCall(function=function)
    #
    #     # Buat ChatResponseStream untuk tool call
    #     message = ChatMessage(
    #         role="assistant",
    #         content="",  # Tool call biasanya tidak memiliki content teks di message utama
    #         tool_calls=[tool_call],
    #     )
    #     # Delta untuk tool call: biasanya tidak ada content, tapi ada tool_calls
    #     # Struktur delta bisa bervariasi tergantung API. Kita sesuaikan dengan yang Anda butuhkan.
    #     # Misalnya, jika API Anda meletakkan tool_calls di dalam delta:
    #     delta = Delta(
    #         role="assistant", content=None, tool_calls=[tool_call]
    #     )  # Sesuaikan struktur ini
    #     choice_stream = ChoiceStream(delta=delta, extra=tool_call_extra)
    #     stream_response = ChatResponseStream(
    #         choices=[choice_stream], usage=Usage(), message=message  # Atau None
    #     )
    #     return stream_response

    async def _process_aresponse_tool(
        self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> ChatResponse | QwenAPIError:
        from .core.types.chat import Choice, Message, Extra

        # Track this session
        self._active_sessions.append(session)

        try:
            extra = None
            text = ""
            async for line in response.content:
                # Check if cancelled
                if self._is_cancelled:
                    self.logger.info("Async tool response processing cancelled")
                    break

                if line.startswith(b"data:"):
                    try:
                        data = json.loads(line[5:].decode())
                        if data["choices"][0]["delta"].get("role") == "function":
                            extra_data = data["choices"][0]["delta"].get("extra")
                            if extra_data:
                                extra = Extra(**extra_data)
                        text += data["choices"][0]["delta"].get("content")
                    except json.JSONDecodeError:
                        continue
            try:
                self.logger.info(f"text: {text}")
                parse_json = json.loads(text)
                if isinstance(parse_json["arguments"], str):
                    parse_arguments = json.loads(parse_json["arguments"])
                else:
                    parse_arguments = parse_json["arguments"]
                self.logger.info(f"parse_json: {parse_json}")
                self.logger.info(f"arguments: {parse_arguments}")
                function = Function(name=parse_json["name"], arguments=parse_arguments)
                message = Message(
                    role="assistant",
                    content="",
                    tool_calls=[ToolCall(function=function)],
                )
                choice = Choice(message=message, extra=extra)
                return ChatResponse(choices=choice)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON response: {e}")
                return QwenAPIError(f"Error decoding JSON response: {e}")

        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            raise

        finally:
            # Remove from active sessions
            if session in self._active_sessions:
                self._active_sessions.remove(session)
            await session.close()

    async def _process_aresponse_tool_from_json(
        self, parsed_json: dict
    ) -> ChatResponse:
        """Process tool response from already parsed JSON data."""
        from .core.types.chat import Choice, Message, Extra
        from .core.types.response.function_tool import Function, ToolCall

        try:
            self.logger.info(f"Processing tool response from JSON: {parsed_json}")

            if isinstance(parsed_json.get("arguments"), str):
                parse_arguments = json.loads(parsed_json["arguments"])
            else:
                parse_arguments = parsed_json.get("arguments", {})

            function = Function(
                name=parsed_json.get("name", ""), arguments=parse_arguments
            )

            message = Message(
                role="assistant",
                content="",
                tool_calls=[ToolCall(function=function)],
            )

            choice = Choice(message=message, extra=None)
            return ChatResponse(choices=choice)

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error processing tool response JSON: {e}")
            raise QwenAPIError(f"Error processing tool response JSON: {e}")

    #
    def _process_stream(
        self, response: requests.Response
    ) -> Generator[ChatResponseStream, None, None]:
        client = SSEClient(response)
        content = ""
        for event in client.events():
            # Check if cancelled
            if self._is_cancelled:
                self.logger.info("Stream processing cancelled")
                break

            if event.data:
                try:
                    data = json.loads(event.data)
                    content += data["choices"][0]["delta"].get("content")
                    yield ChatResponseStream(
                        **data,
                        message=ChatMessage(
                            role=data["choices"][0]["delta"].get("role"),
                            content=content,
                        ),
                    )
                except json.JSONDecodeError:
                    continue

    async def _process_astream(
        self, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> AsyncGenerator[ChatResponseStream, None]:
        # Track this session
        self._active_sessions.append(session)

        try:
            content = ""
            import asyncio

            # Create a task for reading content
            async def read_content():
                async for line in response.content:
                    if self._is_cancelled:
                        break
                    yield line

            # Process stream with cancellation support
            async for line in read_content():
                # Check if cancelled before processing each line
                if self._is_cancelled:
                    self.logger.info("Async stream processing cancelled")
                    break

                if line.startswith(b"data:"):
                    try:
                        data = json.loads(line[5:].decode())
                        content += data["choices"][0]["delta"].get("content")

                        # Yield the chunk
                        yield ChatResponseStream(
                            **data,
                            message=ChatMessage(
                                role=data["choices"][0]["delta"].get("role"),
                                content=content,
                            ),
                        )

                        # Give other coroutines a chance to run and check cancellation
                        await asyncio.sleep(0)

                    except json.JSONDecodeError:
                        continue

        except (aiohttp.ClientError, asyncio.CancelledError) as e:
            if isinstance(e, asyncio.CancelledError):
                self.logger.info("Stream was cancelled")
            else:
                self.logger.error(f"Client error: {e}")
            # Don't re-raise CancelledError, just clean up
            if not isinstance(e, asyncio.CancelledError):
                raise

        finally:
            self.logger.debug(f"Closing session")
            # Remove from active sessions
            if session in self._active_sessions:
                self._active_sessions.remove(session)

            # Force close the session immediately when cancelled
            if not session.closed:
                await session.close()

    def cancel(self):
        """
        Cancel all active requests and close connections.
        """
        self._is_cancelled = True
        self.logger.info("Cancelling all active requests...")

        # Close all active sessions aggressively
        for session in self._active_sessions[
            :
        ]:  # Copy list to avoid modification during iteration
            try:
                if hasattr(session, "close") and not session.closed:
                    # For aiohttp sessions, close immediately
                    if hasattr(session, "_connector") and session._connector:
                        # Force close connector immediately
                        session._connector._ssl_shutdown_timeout = 0.1
                        session._connector.close()

                    # Also try to close the session itself
                    import asyncio

                    if asyncio.iscoroutinefunction(session.close):
                        # Schedule session closure if we're in an async context
                        try:
                            loop = asyncio.get_running_loop()
                            task = loop.create_task(session.close())
                            # Cancel the task immediately to force close
                            task.cancel()
                        except RuntimeError:
                            # No running loop, can't close async session synchronously
                            pass

                    self.logger.debug(f"Session {id(session)} marked for closure")
            except Exception as e:
                # Suppress SSL shutdown timeout warnings as they're expected during cancellation
                if "SSL shutdown timed out" not in str(
                    e
                ) and "CancelledError" not in str(e):
                    self.logger.warning(f"Error closing session {id(session)}: {e}")

        # Clear the sessions list
        self._active_sessions.clear()
        self.logger.info("All active sessions cancelled")

    def close(self):
        """
        Close the client and clean up resources.
        """
        self.cancel()
        self.logger.info("Qwen client closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
