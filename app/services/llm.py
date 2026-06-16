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
        value = json.loads(stripped[start : end + 1])

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
        "每条详情页 Prompt 必须包含中文主标题、副标题、布局、光影、字体、情绪、产品保真约束。"
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
