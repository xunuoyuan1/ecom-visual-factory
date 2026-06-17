# 电商视觉生成系统（LangGraph 架构版）

测试版 MVP，用于把产品图、客户参数和卖点转为 7 屏电商详情图 Prompt。

## 当前范围

- FastAPI 项目入口
- LangGraph 流程构建
- 缺少 LangGraph 依赖时的本地测试 runner
- 产品 State 和 API Schema
- 7 屏策略与 Prompt 生成
- QA 检查与一次修复回路
- 批量 SKU 入口结构

## MVP 验收标准

1. 单 SKU 可以生成 7 屏 Prompt。
2. 信息不足时进入 AI 补全节点，补全字段带 `ai_inference` 来源。
3. 信息充足时跳过补全，直接进入清洗。
4. 每屏 Prompt 包含中文主标题、副标题、布局、光影、字体、情绪、2:3 竖版和产品 1:1 保真约束。
5. QA 能识别高危问题并触发一次 Prompt 修复。
6. 批量入口支持多个 SKU，单个 SKU 输出独立结果。

## 本地测试

当前 Codex 环境未安装 `fastapi`、`langgraph`、`pytest`，可先用 Python 标准库测试核心逻辑：

```powershell
& 'C:\Users\xunuo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests
```

生产或完整开发环境建议安装项目依赖后运行：

```powershell
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

## LLM 模式

默认使用 mock 模式，不会调用 OpenAI，也不会产生模型费用：

```env
LLM_MODE=mock
ENABLE_IMAGE_GENERATION=false
```

切到真实文本模型测试时：

```env
OPENAI_API_KEY=你的 API Key
LLM_MODE=live
VISION_MODEL=gpt-5.4
REASONING_MODEL=gpt-5.5
QA_MODEL=gpt-5.4
IMAGE_MODEL=gpt-image-2
ENABLE_IMAGE_GENERATION=false
```

当前 live 模式已接入 Vision 图片识别、信息补全、7 屏策略、Prompt 生成。Vision QA 和真实生图仍需后续接入；生图开关继续保持关闭，避免测试阶段产生图片生成成本。

## 图片生成

真实图片生成通过 `ENABLE_IMAGE_GENERATION` 单独控制。测试时建议先限制数量：

```env
ENABLE_IMAGE_GENERATION=true
IMAGE_MODEL=gpt-image-2
IMAGE_SIZE=1024x1024
IMAGE_QUALITY=high
IMAGE_GENERATION_TARGETS=asset,detail
MAX_IMAGES_PER_REQUEST=2
```

`IMAGE_GENERATION_TARGETS` 可选：

- `asset`：只生成自定义素材图。
- `detail`：只生成 7 屏详情图。
- `asset,detail`：两类都允许生成，但仍受 `MAX_IMAGES_PER_REQUEST` 限制。
