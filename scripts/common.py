"""共享配置和错误处理；不显示密钥。"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://api.rika-ai.com/v1/api"
ENDPOINTS = {
    "v1": ("/generate", 4),
    "v2": ("/generate-v2", 6),
    "character": ("/generate-character", 1),
    "item": ("/generate-item", 1),
    "map": ("/generate-map", 2),
}


class ClientError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ClientError("无法读取 JSON 文件，请检查路径、权限及 JSON 格式。") from None


def resolve_key(config):
    key = os.environ.get("RIKA_API_KEY", "").strip()
    if not key:
        data = read_json(config)
        if not isinstance(data, dict) or not isinstance(data.get("api_key", ""), str):
            raise ClientError("配置中的 api_key 必须是字符串。", 3)
        key = data.get("api_key", "").strip()
    if not key:
        raise ClientError("API Key 为空，请填写 skill 的 config.json 或设置 RIKA_API_KEY。", 3)
    if any(ord(c) < 33 or ord(c) > 126 for c in key):
        raise ClientError("API Key 含有非法字符。", 3)
    return key
