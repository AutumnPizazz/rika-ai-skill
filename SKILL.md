---
name: rika-ai-skill
description: 调用 Rika AI API 生成像素角色、道具、横板地图和 V1/V2 动画，查询任务并下载结果
keywords: Rika, Rika AI, 像素画, 像素角色, 像素道具, 像素地图, 像素动画, spritesheet
---

# Rika AI

参数与响应见 [references/api.md](references/api.md)。

## 密钥

缺少配置文件时，从 `config.example.json` 复制为 `config.json`，权限设为 600。`config.json` 不纳入 Git。

读取顺序：`RIKA_API_KEY` → `~/.dsh/skills/rika-ai-skill/config.json` 的 `api_key`。为空时让用户填写，不显示密钥，不放进命令参数或请求模板。

```bash
python3 ~/.dsh/skills/rika-ai-skill/scripts/rika.py credits
```

## 生成

| kind | 内容 | 积分 | PNG 参考图 |
|---|---|---|---|
| `v1` | V1 动画 | 4 | 1–3 张：首帧、可选中间帧、可选尾帧 |
| `v2` | V2 动画序列帧 | 6 | 1–3 张，顺序同 V1 |
| `character` | 角色 | 1 | 0–1 张，提示词和图片至少提供一个 |
| `item` | 道具 | 1 | 0–1 张，提示词和图片至少提供一个 |
| `map` | 横板地图 | 2 | 必需的结构图，可再加一张画风参考图 |

按类型复制 `examples/<kind>.json`，修改 `params`。`image_base64` 留空时用 `--image` 传本地 PNG，可重复；已在 JSON 中填入 PNG Data URL 时不再传 `--image`。

```bash
python3 ~/.dsh/skills/rika-ai-skill/scripts/rika.py submit character --payload request.json --dry-run
python3 ~/.dsh/skills/rika-ai-skill/scripts/rika.py submit character --payload request.json --download ./rika-output
```

`--dry-run` 仅离线校验。用户要求实际生成时才提交；缺少必要的提示词或参考图时先询问。

动画图片数量须与 `use_mid_image`、`use_end_image` 一致。单图为 false/false，首尾两图为 false/true，首中尾三图为 true/true。

```bash
python3 ~/.dsh/skills/rika-ai-skill/scripts/rika.py submit v2 --payload request.json --image first.png --image last.png --dry-run
```

V2 的 `pixel_size` 是 `{"x":256,"y":128}` 形式，两轴均为 32–256 内的 32 的倍数，输入 PNG 尺寸必须相符。`ai_expand` 增强提示词，不扩展输入画布。V1、角色、道具的尺寸用字符串，如 `"128"`。

## 查询和下载

提交返回 `gen_id`。`--wait` 持续轮询；`--download DIR` 等待成功后下载结果，已有文件不覆盖。轮询间隔默认 20 秒，客户端等候时限默认 600 秒。

```bash
python3 ~/.dsh/skills/rika-ai-skill/scripts/rika.py job GEN_ID
python3 ~/.dsh/skills/rika-ai-skill/scripts/rika.py job GEN_ID --download ./rika-output --interval 20 --timeout 1200
```

结果地址临时有效，成功后及时下载。客户端超时或中断不取消远端任务，用原 `gen_id` 继续查询。提交时网络失败先查官网任务记录，不直接重提。生成失败或服务器超时会返还积分；客户端等候超时不代表服务器任务超时。

退出码：0 成功；2 参数错误；3 密钥或鉴权错误；4 API 或任务失败；5 网络或文件错误；6 等候超时；130 中断。
