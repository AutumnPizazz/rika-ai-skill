"""固定官方 API 地址；POST 不重试，密钥不随重定向转发。"""
import json
import urllib.error
import urllib.request
from common import BASE_URL, ClientError


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method, endpoint, key, payload=None):
    body = None if payload is None else json.dumps(payload, allow_nan=False).encode()
    req = urllib.request.Request(
        BASE_URL + endpoint, data=body, method=method,
        headers={"Content-Type": "application/json", "X-API-Key": key},
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        hints = {401: "API Key 无效", 403: "无访问权限", 402: "积分不足",
                 404: "接口或任务不存在", 429: "请求过于频繁"}
        raise ClientError(
            f"HTTP {exc.code}：{hints.get(exc.code, 'API 请求失败')}。",
            3 if exc.code in (401, 403) else 4,
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ClientError("网络失败或超时；提交时发生则先查官网任务记录，避免重复扣费。", 5) from None
    except ValueError:
        raise ClientError("API 返回了无法解析的 JSON。", 4) from None
    if not isinstance(result, dict):
        raise ClientError("API 响应不是 JSON 对象。", 4)
    return result
