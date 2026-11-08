"""官网参数的离线校验，完整说明见 references/api.md。"""
import math
from common import ROOT, ENDPOINTS, ClientError, read_json


def validate(kind, params, sizes):
    schema = read_json(ROOT / "references/api-schema.json")
    specs = next(e["requestParams"] for e in schema if e["path"] == ENDPOINTS[kind][0])
    known = {p["name"]: p for p in specs if p["name"] != "image_base64"}
    if set(params) - set(known):
        raise ClientError("params 存在未列入官网文档的字段。")
    enums = {
        "motion_type": ("idle", "walk", "run", "jump", "attack", "hit", "defeated"),
        "attack_type": ("melee", "ranged", "other"),
        "padding_position": ("tl", "tc", "tr", "ml", "mc", "mr", "bl", "bc", "br"),
        "style": ("Retro", "Anime") if kind == "map" else ("None", "Retro", "Anime"),
        "bg_style": ("Parallax", "Flat", "None"),
    }
    for name, val in params.items():
        typ = known[name]["type"]
        valid = {
            "string": isinstance(val, str), "boolean": type(val) is bool,
            "integer": type(val) is int,
            "number": type(val) is int or (type(val) is float and math.isfinite(val)),
            "string | string[]": isinstance(val, str) or (isinstance(val, list) and all(isinstance(v, str) for v in val)),
            "{ x: number; y: number }": isinstance(val, dict),
        }.get(typ, False)
        if not valid or (name in enums and val not in enums[name]):
            raise ClientError(f"params.{name} 类型或取值无效，请查 references/api.md。")
    if not params.get("prompt", "").strip() and (kind not in ("character", "item") or not sizes):
        raise ClientError("此请求需要非空的 params.prompt。")
    if kind in ("v1", "v2"):
        for flag in ("use_mid_image", "use_end_image"):
            if flag not in params and len(sizes) > 1:
                raise ClientError("多张动画图必须显式设置 use_mid_image 和 use_end_image。")
            params.setdefault(flag, False)
        if len(sizes) != 1 + int(params["use_mid_image"]) + int(params["use_end_image"]):
            raise ClientError("参考图数量与中间图、尾图标志不一致。")
    if kind == "v2":
        size = params.get("pixel_size")
        if not isinstance(size, dict) or set(size) != {"x", "y"} or any(
            type(v) is not int or not 32 <= v <= 256 or v % 32 for v in size.values()
        ):
            raise ClientError("V2 pixel_size 需含 x、y，两轴为 32–256 内的 32 的倍数。")
        if any(s != (size["x"], size["y"]) for s in sizes):
            raise ClientError("V2 PNG 尺寸必须与 pixel_size 一致，API 不扩展画布。")
        for name, low, high in (("seed", 0, 2**63 - 1), ("output_frames", 1, 256), ("color_count", 2, 256)):
            if name in params and not low <= params[name] <= high:
                raise ClientError(f"params.{name} 应在 {low}–{high} 内。")
    elif "pixel_size" in params:
        choices = ("32", "64", "128", "256") if kind == "v1" else ("64", "128", "256")
        if params["pixel_size"] not in choices:
            raise ClientError("此接口的 pixel_size 需要使用文档列出的字符串尺寸。")
    if kind == "v1":
        if "length" in params and params["length"] not in (17, 21, 25, 29, 33):
            raise ClientError("V1 length 应为 17、21、25、29 或 33。")
        if "noise_strength" in params and not 0 <= params["noise_strength"] <= 2:
            raise ClientError("V1 noise_strength 应在 0.0–2.0 内。")
