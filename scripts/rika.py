#!/usr/bin/env python3
"""Rika AI 命令行入口；仅使用 Python 标准库。"""
import argparse
import json
import math
from pathlib import Path
import sys
import urllib.error
import api
import jobs
import payload
from common import ROOT, BASE_URL, ENDPOINTS, ClientError, resolve_key


def positive(value):
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("必须是大于 0 的秒数。") from None
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("必须是大于 0 的秒数。")
    return number


def parse(argv):
    parser = argparse.ArgumentParser(description="Rika AI 像素生成 API；submit 消耗积分。")
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("credits", help="查询积分余额")
    submit = commands.add_parser("submit", help="创建生成任务，不自动重试")
    submit.add_argument("kind", choices=ENDPOINTS)
    submit.add_argument("--payload", required=True, type=Path)
    submit.add_argument("--image", action="append", default=[], type=Path, help="按顺序添加 PNG，可重复")
    submit.add_argument("--dry-run", action="store_true", help="离线校验，不读密钥、不联网")
    job = commands.add_parser("job", help="查询已有任务")
    job.add_argument("gen_id")
    for sub in (submit, job):
        sub.add_argument("--wait", action="store_true", help="轮询至成功或失败")
        sub.add_argument("--interval", type=positive, default=20, help="轮询间隔秒数，默认 20")
        sub.add_argument("--timeout", type=positive, default=600, help="客户端等候秒数，默认 600")
        sub.add_argument("--download", type=Path, metavar="DIR", help="等候成功后下载到目录，隐含 --wait")
    return parser.parse_args(argv)


def run(args):
    data = payload.build(args.kind, args.payload, args.image) if args.command == "submit" else None
    if args.command == "submit" and args.dry_run:
        summary = {**data, "image_base64": ["<PNG omitted>" for _ in data["image_base64"]]}
        return {"method": "POST", "url": BASE_URL + ENDPOINTS[args.kind][0],
                "credits": ENDPOINTS[args.kind][1], "payload": summary}
    if args.command == "job":
        jobs.job_id(args.gen_id)
    key = resolve_key(args.config)
    if args.command == "credits":
        return api.request("GET", "/credits", key)
    if args.command == "submit":
        result = api.request("POST", ENDPOINTS[args.kind][0], key, data)
        gen_id = jobs.job_id(result.get("gen_id"))
        print(f"任务已创建：gen_id={gen_id}", file=sys.stderr)
        if not (args.wait or args.download):
            return result
    else:
        gen_id = args.gen_id
    result = jobs.get_job(gen_id, key, args.wait or bool(args.download), args.interval, args.timeout)
    if args.download and result.get("status") == "succeeded":
        result["local_files"] = jobs.download(result, gen_id, args.download)
    return result


def main(argv=None):
    args = parse(argv)
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 4 if result.get("status") == "failed" else 0
    except ClientError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except (OSError, urllib.error.URLError):
        print("文件读写或下载失败；已有任务可用 job 命令继续处理，已有文件不会覆盖。", file=sys.stderr)
        return 5
    except KeyboardInterrupt:
        print("客户端已停止，已提交的任务仍可用 job 命令查询。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
