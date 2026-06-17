import json
from typing import Any

from app.config import settings
from app.graph.state import ProductState
from app.prompts.constants import SCREEN_FLOW


class LLMServiceError(RuntimeError):
    """Raised when a live LLM call cannot return usable structured data."""


def should_use_live_llm() -> bool:
    return settings.llm_mode.lower() == "live" and bool(settings.openai_api_key)


def _client() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMServiceError("openai package is not installed") from exc

    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    if chunks:
        return "\n".join(chunks)

    raise LLMServiceError("OpenAI response did not include output text")


def _clean_trailing_commas(text: str) -> str:
    """Remove trailing commas before } or ] but only outside JSON string values."""
    result: list[str] = []
    in_string = False
    escaped = False
    i = 0

    while i < len(text):
        ch = text[i]

        if escaped:
            result.append(ch)
            escaped = False
            i += 1
            continue

        if ch == "\\" and in_string:
            result.append(ch)
            escaped = True
            i += 1
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue

        if ch == "," and not in_string:
            j = i + 1
            while j < len(text) and text[j].isspace():
                j += 1
            if j < len(text) and text[j] in "}]":
                i += 1
                continue

        result.append(ch)
        i += 1

    return "".join(result)


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()

    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMServiceError("LLM response did not contain JSON")
        value = json.loads(_clean_trailing_commas(stripped[start : end + 1]))

    if not isinstance(value, dict):
        raise LLMServiceError("LLM JSON response must be an object")
    return value


def _json_call(model: str, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
    response = _client().responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "请只输出一个合法 JSON 对象，不要使用 Markdown。\n"
                    f"{json.dumps(user_payload, ensure_ascii=False)}"
                ),
            },
        ],
    )
    return _extract_json(_response_text(response))


def _vision_json_call(
    model: str,
    system_prompt: str,
    text_payload: dict[str, Any],
    images: list[str],
    image_roles: list[str],
) -> dict[str, Any]:
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                "请只输出一个合法 JSON 对象，不要使用 Markdown。\n"
                f"{json.dumps(text_payload, ensure_ascii=False)}"
            ),
        }
    ]
    for index, image in enumerate(images):
        role = image_roles[index] if index < len(image_roles) else "other"
        content.append({"type": "input_text", "text": f"图片 {index + 1} 角色：{role}"})
        content.append({"type": "input_image", "image_url": image})

    response = _client().responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
    )
    return _extract_json(_response_text(response))


def parse_product_images(state: ProductState) -> dict[str, Any]:
    images = state.get("images", [])
    if not images:
        raise LLMServiceError("vision parsing requires at least one image")

    system_prompt = (
        "你是电商产品视觉识别专家。任务：识别图片文字 OCR，提取包装设计、产品结构、材质特征、"
        "目标用户推断、潜在卖点和置信度。禁止编造包装文字、认证、品牌事实、专利或功效。"
        "输出 JSON，必须包含 raw_ocr, visual_elements, packaging, text_detected, materials_guess, "
        "design_features, selling_signals, user_guess, confidence。所有不确定内容必须标低置信度。"
    )
    payload = {
        "product_name": state.get("product_name", ""),
        "brand_from_user": state.get("brand", ""),
        "product_type_from_user": state.get("product_type", ""),
        "target_market": state.get("target_market", ""),
        "output_language": state.get("output_language", ""),
        "user_specs": state.get("user_specs", {}),
        "user_selling_points": state.get("user_selling_points", []),
        "image_roles": state.get("image_roles", []),
    }
    data = _vision_json_call(
        settings.vision_model,
        system_prompt,
        payload,
        images,
        state.get("image_roles", []),
    )

    required = {
        "raw_ocr",
        "visual_elements",
        "packaging",
        "text_detected",
        "materials_guess",
        "design_features",
        "selling_signals",
        "user_guess",
        "confidence",
    }
    missing = sorted(required - set(data))
    if missing:
        raise LLMServiceError(f"vision response missing fields: {', '.join(missing)}")
    return data


def complete_product_data(state: ProductState) -> dict[str, Any]:
    system_prompt = (
        "你是电商产品信息架构师。只补全缺失字段，不得编造品牌事实、认证、专利、真实成分或平台资质。"
        "每个字段必须保留 value/source/confidence 结构，source 使用 ai_inference。"
    )
    payload = {
        "merged_data": state.get("merged_data", {}),
        "missing_fields": state.get("missing_fields", []),
        "product_name": state.get("product_name", ""),
        "target_market": state.get("target_market", ""),
        "output_language": state.get("output_language", ""),
        "user_selling_points": state.get("user_selling_points", []),
    }
    data = _json_call(settings.reasoning_model, system_prompt, payload)
    completed = data.get("completed_data", data)
    if not isinstance(completed, dict):
        raise LLMServiceError("completed_data must be an object")
    return completed


def generate_visual_strategy(state: ProductState) -> dict[str, Any]:
    system_prompt = (
        "你是电商视觉总监。基于结构化产品数据和市场数据，设计7屏详情图策略。"
        "必须符合认知、兴趣、信任、理性、场景、信任强化、决策路径。"
        "输出 JSON，键名必须是 screen_1 到 screen_7。每屏包含 screen_goal, core_selling_point, "
        "forbidden_content, visual_style, font_style, emotion。不得重复主信息。"
    )
    payload = {
        "cleaned_data": state.get("cleaned_data", {}),
        "market_data": state.get("market_data", {}),
        "target_market": state.get("target_market", ""),
        "output_language": state.get("output_language", ""),
        "screen_flow": SCREEN_FLOW,
    }
    data = _json_call(settings.reasoning_model, system_prompt, payload)
    strategy = data.get("strategy", data)
    if not isinstance(strategy, dict):
        raise LLMServiceError("strategy must be an object")
    missing = [f"screen_{i}" for i in range(1, 8) if f"screen_{i}" not in strategy]
    if missing:
        raise LLMServiceError(f"strategy missing screens: {', '.join(missing)}")
    return strategy


def generate_prompts(state: ProductState) -> dict[str, Any]:
    generation_mode = state.get("generation_mode", "smart_detail")
    include_detail_screens = state.get("include_detail_screens", False)
    system_prompt = (
        "你是顶级电商视觉导演和 AI 提示词工程师。根据 generation_mode 生成 Prompt。"
        "detail_prompts 用 screen_1 到 screen_7；asset_prompts 按素材类型输出字符串数组。"
        "7屏详情页和单图素材必须分开字段，平台主图规则只应用于对应素材类型，不得污染7屏详情页。"
        "每条详情页 Prompt 必须包含主标题、副标题、布局、光影、字体、情绪、产品保真约束。"
        "所有生成图片中出现的可见文字，包括主标题、副标题、卖点文案、标签、按钮和屏幕 UI 文案，必须使用 output_language 指定语言。"
        "Prompt 说明本身可以中文，但画面可见文字必须匹配 output_language；例如 output_language=English 时，不要生成中文标题文案。"
        "如果产品是智能手表、智能屏幕设备或电子屏产品，asset_prompts 必须要求屏幕点亮并显示通用非品牌化 UI，"
        "可包含时间、步数、心率趋势、运动记录、消息提醒等；不得出现 Apple、Apple Watch、任何品牌 Logo、"
        "医疗诊断、FDA、clinical、100% accurate 或血压精确诊断。"
        "主图仍遵守平台合规边界，但要通过屏幕 UI、棚拍高光、轻微 3/4 角度提升质感；"
        "场景图和广告图要更有生活方式与科技感，不要只做平铺白底。"
        "输出 JSON 对象，可包含 detail_prompts, prompts, asset_prompts。"
    )
    payload = {
        "generation_mode": generation_mode,
        "include_detail_screens": include_detail_screens,
        "cleaned_data": state.get("cleaned_data", {}),
        "strategy": state.get("strategy", {}),
        "asset_plan": state.get("asset_plan", []),
        "asset_prompts_existing": state.get("asset_prompts", {}),
        "platform_rules_applied": state.get("platform_rules_applied", {}),
        "user_constraints": state.get("user_constraints", {}),
        "target_market": state.get("target_market", ""),
        "output_language": state.get("output_language", ""),
    }
    data = _json_call(settings.reasoning_model, system_prompt, payload)
    result: dict[str, Any] = {}

    if generation_mode == "smart_detail":
        detail_prompts = data.get("detail_prompts") or data.get("prompts")
        if not isinstance(detail_prompts, dict) or len(detail_prompts) != 7:
            raise LLMServiceError("smart_detail requires 7 detail_prompts")
        result["detail_prompts"] = detail_prompts
        result["prompts"] = detail_prompts
        result["asset_prompts"] = {}
    elif generation_mode == "custom_assets":
        asset_prompts = data.get("asset_prompts", state.get("asset_prompts", {}))
        if not isinstance(asset_prompts, dict):
            raise LLMServiceError("custom_assets requires asset_prompts object")
        result["asset_prompts"] = asset_prompts
        if include_detail_screens:
            detail_prompts = data.get("detail_prompts") or data.get("prompts")
            if not isinstance(detail_prompts, dict) or len(detail_prompts) != 7:
                raise LLMServiceError("custom_assets include_detail_screens requires 7 detail_prompts")
            result["detail_prompts"] = detail_prompts
            result["prompts"] = detail_prompts
        else:
            result["detail_prompts"] = {}
            result["prompts"] = {}
    else:
        detail_prompts = data.get("detail_prompts") or data.get("prompts")
        asset_prompts = data.get("asset_prompts", state.get("asset_prompts", {}))
        if not isinstance(detail_prompts, dict) or len(detail_prompts) != 7:
            raise LLMServiceError("hybrid requires 7 detail_prompts")
        if not isinstance(asset_prompts, dict):
            raise LLMServiceError("hybrid requires asset_prompts object")
        result["detail_prompts"] = detail_prompts
        result["prompts"] = detail_prompts
        result["asset_prompts"] = asset_prompts

    return result


def generate_image(prompt: str, image_id: str, image_type: str) -> dict[str, Any]:
    try:
        response = _client().images.generate(
            model=settings.image_model,
            prompt=prompt,
            size=settings.image_size,
            quality=settings.image_quality,
            n=1,
        )
    except Exception as exc:
        raise LLMServiceError(f"image generation failed for {image_id}: {exc}") from exc

    data = getattr(response, "data", None)
    if not data:
        raise LLMServiceError(f"image generation returned no data for {image_id}")

    first = data[0]
    b64_json = getattr(first, "b64_json", None)
    image_url = getattr(first, "url", None)
    revised_prompt = getattr(first, "revised_prompt", None)
    if not b64_json and not image_url:
        raise LLMServiceError(f"image generation returned no image payload for {image_id}")

    return {
        "id": image_id,
        "type": image_type,
        "model": settings.image_model,
        "size": settings.image_size,
        "quality": settings.image_quality,
        "prompt": prompt,
        "b64_json": b64_json,
        "url": image_url,
        "revised_prompt": revised_prompt,
        "error": None,
    }
