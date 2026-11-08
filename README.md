# rika-ai-skill

用于 dsh 的 [Rika AI](https://rika-ai.com/zh/api/) skill，生成像素角色、道具、横板地图和动画，查询任务并下载结果。也可直接使用附带的 Python 命令行工具。

仅使用 Python 3 标准库，无需安装第三方依赖。调用生成接口需要 Rika AI 的 API Key 和积分。

## 安装到 dsh

将仓库克隆或下载到本地，在仓库根目录执行。以下命令适用于 Linux 和 macOS：

```bash
mkdir -p "$HOME/.dsh/skills"
ln -s "$(pwd)" "$HOME/.dsh/skills/rika-ai-skill"
```

在 dsh 中搜索并加载 `rika-ai-skill`。技能调用说明见 [SKILL.md](SKILL.md)。

## 配置密钥

在 Rika AI 的 API 页面创建密钥，然后在仓库根目录执行：

```bash
test -e config.json || cp config.example.json config.json
chmod 600 config.json
```

编辑 `config.json`，将 `api_key` 的空字符串替换为自己的密钥：

```json
{
  "api_key": ""
}
```

也可通过环境变量 `RIKA_API_KEY` 提供密钥，环境变量优先于配置文件。`config.json` 已被 Git 忽略；不要将密钥填入 `config.example.json`、请求模板或提交到仓库。

查询余额：

```bash
python3 scripts/rika.py credits
```

使用其他位置的配置文件时，将 `--config` 放在子命令前：

```bash
python3 scripts/rika.py --config /path/to/config.json credits
```

## 生成素材

| kind | 生成内容 | 每次积分 | PNG 参考图 |
|---|---|---|---|
| `v1` | V1 动画 | 4 | 1–3 张：首帧、可选中间帧、可选尾帧 |
| `v2` | V2 动画序列帧 | 6 | 1–3 张，顺序同 V1 |
| `character` | 角色 | 1 | 0–1 张，提示词和参考图至少提供一个 |
| `item` | 道具 | 1 | 0–1 张，提示词和参考图至少提供一个 |
| `map` | 横板地图 | 2 | 必需的结构图，可再加一张画风参考图 |

费用以 Rika AI 官方页面为准。本项目不提供积分，也不改变服务端计费。

以生成角色为例，复制模板并修改 `params` 中的提示词、画风和尺寸：

```bash
cp examples/character.json /tmp/rika-character.json
python3 scripts/rika.py submit character --payload /tmp/rika-character.json --dry-run
```

`--dry-run` 只做离线校验，不读取密钥、不联网。确认参数后去掉该选项，提交任务并等待下载：

```bash
python3 scripts/rika.py submit character --payload /tmp/rika-character.json --download /tmp/rika-output
```

`--image` 接受本地 PNG 路径，可重复传入。使用它时，请求 JSON 中的 `image_base64` 应为空；也可以直接在该数组中提供完整的 PNG Data URL。

V2 模板使用三张 256×128 PNG，按首帧、中间帧、尾帧的顺序传入：

```bash
python3 scripts/rika.py submit v2 --payload examples/v2.json --image first.png --image middle.png --image last.png --dry-run
```

动画的 `use_mid_image`、`use_end_image` 必须与图片数量对应：单图为 false/false，首尾两图为 false/true，首中尾三图为 true/true。V2 的 `pixel_size` 为 `{"x":256,"y":128}` 形式，两轴均为 32–256 内的 32 的倍数，输入 PNG 尺寸必须相符。`ai_expand` 增强动作提示词，不扩展输入画布。

其他类型的模板在 [examples/](examples/)，完整字段和响应见 [接口参考](references/api.md)。

## 查询任务和下载结果

提交成功后返回 `gen_id`。不加 `--wait` 或 `--download` 时，客户端提交后立即退出。

```bash
python3 scripts/rika.py job GEN_ID
python3 scripts/rika.py job GEN_ID --download /tmp/rika-output --timeout 1200
```

`--wait` 轮询至成功或失败；`--download DIR` 包含等待，并在成功后保存结果。轮询间隔 `--interval` 默认 20 秒，客户端等候时限 `--timeout` 默认 600 秒。

结果 URL 临时有效，应及时下载；下载不覆盖同名文件。客户端超时或中断不取消远端任务，使用原 `gen_id` 继续查询。提交时网络失败先检查官网任务记录，不直接重新提交；客户端不会自动重试提交请求。

## 测试

```bash
python3 -B scripts/selftest.py
```

测试完全离线，不读取真实密钥，不创建付费任务。

## 许可证

[MIT](LICENSE)。Rika AI 服务及生成内容另受其服务条款约束。
