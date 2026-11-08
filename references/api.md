# Rika AI 接口

文档：https://rika-ai.com/zh/api/

基础地址：`https://api.rika-ai.com/v1/api`。请求头：`Content-Type: application/json`、`X-API-Key: <API_KEY>`。

生成请求的顶层字段为 `image_base64` 和 `params`；下表除 `image_base64` 外均为 `params` 内的字段。图片使用 PNG Data URL：`data:image/png;base64,...`。

所有生成接口返回 `{"gen_id":"..."}`。通过 `GET /jobs/{gen_id}` 查询状态，成功后从 `output_images[].url` 下载结果。V2 返回一个 PNG spritesheet。

结果地址不会长期保存。生成失败或服务器超时自动返还积分。V2 的 `ai_expand` 用于增强提示词，API 不扩展图片画布。

## GET /credits

获取当前积分余额

### 响应字段

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `credits` | 是 | `number` | 当前积分余额 |

## POST /generate

生成 V1 像素动画（4 积分）

请求模板：[examples/v1.json](../examples/v1.json)。

### 请求参数

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `image_base64` | 是 | `string[]` | 1–3 张 PNG；Base64 PNG 图片，顺序为起始图、可选中间图、可选结尾图；引用开关应与实际图片一致。 |
| `prompt` | 是 | `string` | 动画文本描述 |
| `motion_type` | 否 | `string` | idle \| walk \| run \| jump \| attack \| hit \| defeated；动作类型（默认 idle） |
| `pixel_size` | 否 | `string` | 32 \| 64 \| 128 \| 256；像素尺寸（默认 128） |
| `seed` | 否 | `number` | 随机种子 |
| `attack_type` | 否 | `string` | melee \| ranged \| other；motion_type 为 attack 时的攻击子类型 |
| `noise_strength` | 否 | `number` | 0.0–2.0，服务器默认 0.8；应用于两个模型层级的噪声强度；网页默认 0.6。 |
| `length` | 否 | `integer` | 17 \| 21 \| 25 \| 29 \| 33；原始长度参数：2 × 目标输出帧数 + 1，对应网页的 8/10/12/14/16 帧预设 |
| `use_mid_image` | 否 | `boolean` | 是否使用中间参考图 |
| `use_end_image` | 否 | `boolean` | 是否使用结尾参考图 |
| `use_padding` | 否 | `boolean` | 提交图片是否包含 V1 扩展画布 |
| `padding_position` | 否 | `string` | tl \| tc \| tr \| ml \| mc \| mr \| bl \| bc \| br；内容在扩展画布中的位置 |
| `scale_factor` | 否 | `number` | 用于准备模型输入的像素放大倍率 |

## POST /generate-v2

生成 V2 像素动画序列帧（6 积分）

请求模板：[examples/v2.json](../examples/v2.json)。

### 请求参数

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `image_base64` | 是 | `string[]` | 1–3 张 PNG；直接提供 pixel_size 尺寸的图片；API 不执行扩展画布。顺序与 V1 相同：首帧、可选中间帧、可选尾帧，并设置两个对应标志。 |
| `prompt` | 是 | `string` | 动画动作描述 |
| `pixel_size` | 是 | `{ x: number; y: number }` | 32–256，32 的倍数；每张输入图片的逻辑像素尺寸。 |
| `ai_expand` | 否 | `boolean` | 默认 true；结合参考图与原始动作描述生成分时段提示词并自动选择动作配置；历史与公开参数仍保留原始提示词。 |
| `seed` | 否 | `integer` | 0–2^63-1；随机种子；省略时由服务器生成 |
| `output_frames` | 否 | `integer` | API 为 1–256，默认 24；网页预设为 16 / 20 / 24 / 32；最终序列帧数量。 |
| `color_count` | 否 | `integer` | 2–256；128×128 时默认 128，其他尺寸默认 64；后处理调色盘的最大颜色数量 |
| `use_mid_image` | 否 | `boolean` | 显式设置；是否提供中间参考图；有则放在首帧之后。 |
| `use_end_image` | 否 | `boolean` | 显式设置；是否提供结尾参考图；有则放在中间帧之后。两个标志都省略时沿用旧版 V2 的参考图顺序。 |

## POST /generate-character

生成像素角色（1 积分）

请求模板：[examples/character.json](../examples/character.json)。

### 请求参数

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `image_base64` | 否 | `string[]` | 0–1 张 PNG；可选形象参考图；提示词和参考图至少提供一个。 |
| `prompt` | 否 | `string` | 角色描述；已提供参考图时可为空。 |
| `pixel_size` | 否 | `string` | 64 \| 128 \| 256；像素尺寸（默认 128） |
| `style` | 否 | `string` | None \| Retro \| Anime；角色画风 |
| `domain_color` | 否 | `string \| string[]` | 十六进制颜色；角色主导色 |

## POST /generate-item

生成像素道具（1 积分）

请求模板：[examples/item.json](../examples/item.json)。

### 请求参数

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `image_base64` | 否 | `string[]` | 0–1 张 PNG；可选道具参考图；提示词和参考图至少提供一个。 |
| `prompt` | 否 | `string` | 道具外观与材质描述 |
| `pixel_size` | 否 | `string` | 64 \| 128 \| 256；像素尺寸（默认：128） |
| `style` | 否 | `string` | None \| Retro \| Anime；道具画风 |
| `domain_color` | 否 | `string \| string[]` | 十六进制颜色；道具主导色 |

## POST /generate-map

生成横板像素地图（2 积分）

请求模板：[examples/map.json](../examples/map.json)。

### 请求参数

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `image_base64` | 是 | `string[]` | 1–2 张 PNG；第一张为必需的关卡结构图，第二张为可选的画风参考图。 |
| `prompt` | 是 | `string` | 地图环境与视觉描述 |
| `style` | 否 | `string` | Retro \| Anime；地图像素画风 |
| `bg_style` | 否 | `string` | Parallax \| Flat \| None；背景类型 |
| `domain_color` | 否 | `string \| string[]` | 十六进制颜色；地图主导色 |

## GET /jobs/{gen_id}

获取任务状态和结果

### 响应字段

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `gen_id` | 是 | `string` | 任务 ID |
| `job_type` | 是 | `string` | 任务类型 |
| `status` | 是 | `string` | queued\|running\|succeeded\|failed；当前状态 |
| `animation_version` | 否 | `number` | 1 \| 2；动画管线版本 |
| `processing_stage` | 否 | `string \| null` | prompt_optimization \| generation_starting \| generating；V2 当前或最后记录的处理阶段 |
| `input_params` | 是 | `object` | 用户可见的输入参数；内部运行元数据不会返回 |
| `output_params` | 否 | `object` | 结果元数据 |
| `created_at` | 是 | `string` | 创建时间戳 |
| `updated_at` | 否 | `string` | 最后更新时间戳 |
| `input_images` | 否 | `object[]` | 输入图片列表 |
| `output_images` | 否 | `object[]` | 生成资源列表 |
| `persist_images` | 否 | `boolean` | 图片是否持久化存储 |
| `liked` | 否 | `boolean` | 用户是否点赞 |
| `error` | 否 | `string` | 失败时的错误信息 |

### 响应示例

```json
{
  "gen_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "animation",
  "status": "succeeded",
  "animation_version": 2,
  "processing_stage": "generating",
  "input_params": {},
  "output_params": {},
  "created_at": "2026-10-10T12:00:00Z",
  "updated_at": "2026-10-10T12:02:00Z",
  "input_images": [],
  "output_images": [
    { "url": "https://cdn.rika-ai.com/...", "key": "..." }
  ],
  "persist_images": false,
  "liked": false,
  "error": null
}
```
