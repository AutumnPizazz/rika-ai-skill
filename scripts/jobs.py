"""轮询已有任务并下载临时结果；下载请求不携带 API Key。"""
from pathlib import Path
import re
import shutil
import time
import urllib.parse
import urllib.request
import api
from common import ClientError


def job_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
        raise ClientError("gen_id 格式无效。")
    return value


def get_job(gen_id, key, wait=False, interval=20, timeout=600):
    deadline = time.monotonic() + timeout
    while True:
        job = api.request("GET", "/jobs/" + job_id(gen_id), key)
        status = job.get("status")
        if status not in ("queued", "running", "succeeded", "failed"):
            raise ClientError("API 返回了未识别的任务状态。", 4)
        if not wait or status in ("succeeded", "failed"):
            return job
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ClientError("客户端等候超时，任务未取消；使用 job 命令继续查询，勿重复提交。", 6)
        time.sleep(min(interval, remaining))


def check_url(url):
    if not isinstance(url, str):
        raise ClientError("结果缺少下载地址。", 4)
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ClientError("下载地址必须是无账号信息的 HTTPS URL。", 4)


class DownloadRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(job, gen_id, directory):
    if job.get("status") != "succeeded":
        raise ClientError("任务尚未成功，无法下载。", 4)
    images = job.get("output_images")
    if not isinstance(images, list) or not images:
        raise ClientError("成功任务没有返回 output_images。", 4)
    gen_id = job_id(gen_id)
    directory = Path(directory).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    files = []
    for index, image in enumerate(images, 1):
        url = image.get("url") if isinstance(image, dict) else None
        check_url(url)
        req = urllib.request.Request(url, headers={"User-Agent": "dsh-rika-ai/1"})
        with urllib.request.build_opener(DownloadRedirect()).open(req, timeout=60) as response:
            ext = Path(urllib.parse.urlsplit(url).path).suffix.lower()
            if ext not in (".png", ".gif", ".webp", ".jpg", ".jpeg", ".zip"):
                ext = ".bin"
            path = directory / f"{gen_id}-{index:03d}{ext}"
            with path.open("xb") as target:
                try:
                    shutil.copyfileobj(response, target)
                except BaseException:
                    target.close()
                    path.unlink(missing_ok=True)
                    raise
            files.append(str(path.resolve()))
    return files
