import json
import re
from typing import Dict, Any

# asumsi kamu punya ChatMessage class seperti sebelumnya
# from your_module import ChatMessage, EndpointAPI, QwenAPIError, RateLimitError


def _strip_code_fences(s: str) -> str:
    """
    Hilangkan ```json ... ``` atau ``` ... ``` di sekitar output, jika ada.
    """
    s = s.strip()
    fence = re.compile(r"^```[a-zA-Z0-9]*\s*([\s\S]*?)\s*```$", re.MULTILINE)
    m = fence.match(s)
    return m.group(1).strip() if m else s


def _extract_json_object(s: str) -> str:
    """
    Ambil substring JSON {...} pertama jika model nyampur teks lain.
    """
    # cepat: cari block { ... } paling luar
    # ini naive tapi praktis; kalau gagal, balikin string asli
    start = s.find("{")
    if start == -1:
        return s
    # scan balance brace
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return s  # fallback


def _safe_parse_choice(content: str) -> Dict[str, bool | str]:
    """
    Parse output model jadi dict {"use_tools": bool, "tool_name": str}
    Tangani berbagai kemungkinan format yang 'nakal'.
    """
    raw = _strip_code_fences(content)
    raw = _extract_json_object(raw)

    try:
        obj = json.loads(raw)
    except Exception:
        # fallback: coba perbaiki boolean format (true/false) jika jadi string kapital dsb
        fixed = raw.replace("True", "true").replace("False", "false")
        obj = json.loads(fixed)

    if not isinstance(obj, dict):
        raise ValueError("Model output is not a JSON object")

    # validasi minimal
    if "use_tools" not in obj or "tool_name" not in obj:
        raise ValueError("Missing required keys: use_tools/tool_name")

    # normalisasi
    use_tools = bool(obj["use_tools"])
    tool_name = str(obj["tool_name"]).strip()

    # tool_name harus "none" kalau use_tools False
    if not use_tools:
        tool_name = "none"

    return {"use_tools": use_tools, "tool_name": tool_name}
