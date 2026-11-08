"""加载请求 JSON，将本地 PNG 编为 Data URL。"""
import base64
import binascii
from pathlib import Path
import struct
from common import ClientError, read_json
from rules import validate


def png_size(data):
    if len(data) < 24 or data[:8] != bytes((137, 80, 78, 71, 13, 10, 26, 10)) or data[12:16] != b"IHDR":
        raise ClientError("参考图必须是 PNG；客户端检查 PNG 文件头和尺寸。")
    size = struct.unpack(">II", data[16:24])
    if not all(size):
        raise ClientError("PNG 图片尺寸无效。")
    return size


def build(kind, filename, images):
    payload = read_json(filename)
    if not isinstance(payload, dict) or set(payload) - {"image_base64", "params"}:
        raise ClientError("请求体只支持顶层 image_base64 和 params。")
    params = payload.setdefault("params", {})
    encoded = payload.setdefault("image_base64", [])
    if not isinstance(params, dict) or not isinstance(encoded, list):
        raise ClientError("params 必须是对象，image_base64 必须是数组。")
    if images and encoded:
        raise ClientError("--image 与非空 image_base64 不能同时使用。")
    for image in images:
        data = Path(image).read_bytes()
        png_size(data)
        encoded.append("data:image/png;base64," + base64.b64encode(data).decode("ascii"))
    sizes = []
    for image in encoded:
        if not isinstance(image, str) or not image.startswith("data:image/png;base64,"):
            raise ClientError("参考图需为 data:image/png;base64,... 格式。")
        try:
            data = base64.b64decode(image.split(",", 1)[1], validate=True)
        except (binascii.Error, ValueError):
            raise ClientError("图片 Base64 编码无效。") from None
        sizes.append(png_size(data))
    low, high = (0, 1) if kind in ("character", "item") else ((1, 2) if kind == "map" else (1, 3))
    if not low <= len(sizes) <= high:
        raise ClientError(f"{kind} 需要 {low}–{high} 张 PNG 参考图。")
    validate(kind, params, sizes)
    return payload
