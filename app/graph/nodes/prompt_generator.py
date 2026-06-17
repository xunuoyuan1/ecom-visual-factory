from app.graph.state import ProductState
from app.prompts.constants import SCREEN_FLOW
from app.data.platform_rules import PLATFORM_RULES, ASSET_TYPES
from app.prompts.enhancers import enhance_asset_prompt
from app.services import llm


def _build_detail_prompts(state: ProductState) -> dict[str, str]:
    """Build detail screen prompts from the visual strategy."""
    cleaned = state.get("cleaned_data", {})
    strategy = state.get("strategy", {})
    brand = cleaned.get("brand", {}).get("value") or "产品"
    product_type = cleaned.get("product_type", {}).get("value") or "商品"

    # Use aspect_ratio from user_constraints, default to "2:3"
    aspect_ratio = (
        state.get("user_constraints", {}).get("aspect_ratio") or "2:3"
    )
    aspect_str = f"{aspect_ratio}竖版" if ":" in aspect_ratio and "竖" not in aspect_ratio else aspect_ratio

    detail_prompts = {}
    for screen_key, plan in strategy.items():
        title = f"{brand}{product_type}"
        subtitle = plan["core_selling_point"]
        detail_prompts[screen_key] = (
            f"主标题：{title}\n"
            f"副标题：{subtitle}\n"
            f"屏幕目标：{plan['screen_goal']}\n"
            f"布局说明：{aspect_str}详情图，产品主体居中偏上，标题位于上方安全区，"
            "副标题靠近产品但不遮挡包装文字，底部保留留白用于转化信息。\n"
            "光影描述：柔和主光源，高级商业摄影质感，包装边缘清晰，"
            "避免过曝和阴影遮挡文字。\n"
            f"字体风格：{plan['font_style']}，中文排版清晰，字重有层级。\n"
            f"情绪风格：{plan['emotion']}。\n"
            f"视觉风格：{plan['visual_style']}。\n"
            f"禁止内容：{', '.join(plan['forbidden_content'])}。\n"
            "严格还原上传的产品图，包括包装设计、颜色、LOGO位置、文字内容、"
            "图案元素等所有细节。"
        )
    return detail_prompts


def _build_asset_prompts(state: ProductState) -> dict[str, list[str]]:
    """Build asset prompts for hybrid mode (same style as asset_planning)."""
    platform_key = (
        state.get("user_constraints", {})
        .get("platform", "tmall")
        .lower()
        .replace(" ", "_")
    )
    platform_map = {
        "amazon": "amazon", "tiktok shop": "tiktok_shop",
        "tiktokshop": "tiktok_shop", "shopee": "shopee",
        "temu": "temu", "lazada": "lazada", "jd": "jd",
        "京东": "jd", "taobao": "taobao", "淘宝": "taobao",
        "tmall": "tmall", "天猫": "tmall",
        "alibaba": "alibaba", "阿里国际站": "alibaba",
    }
    platform_key = platform_map.get(platform_key, platform_key)
    platform_rules = PLATFORM_RULES.get(platform_key, {})

    image_rules = platform_rules.get("image_rules", {})

    requested_types = state.get("asset_types_requested", [])
    if not requested_types:
        requested_types = [{"type_name": t, "count": 1} for t in ASSET_TYPES]

    asset_prompts = {}
    for req in requested_types:
        type_name = req["type_name"]
        if type_name == "7屏详情页":
            continue
        count = int(req.get("count", 1))
        type_rules = image_rules.get(type_name, {})
        actual_count = min(count, type_rules.get("max_count", 999))

        asset_prompts[type_name] = [
            enhance_asset_prompt(
                state,
                type_name,
                f"[{type_name}] ({platform_rules.get('name', platform_key)}) "
                f"{type_rules.get('recommended', '1200x1200')} "
                f"{type_rules.get('aspect_ratio', '1:1')} "
                f"产品描述：{state.get('product_name', '待填产品')} - 第{n+1}张",
            )
            for n in range(actual_count)
        ]
    return asset_prompts


def prompt_generator(state: ProductState) -> dict:
    if llm.should_use_live_llm():
        try:
            result = llm.generate_prompts(state)
            result["llm_mode_used"] = "live"
            return result
        except llm.LLMServiceError as exc:
            errors = list(state.get("errors", []))
            errors.append({"node": "prompt_generator", "severity": "medium", "message": str(exc)})
            result = _mock_prompt_generator(state)
            result["errors"] = errors
            result["llm_mode_used"] = "mock_fallback"
            return result

    return _mock_prompt_generator(state)


def _mock_prompt_generator(state: ProductState) -> dict:
    generation_mode = state.get("generation_mode", "smart_detail")
    include_detail_screens = state.get("include_detail_screens", False)

    result: dict = {}

    if generation_mode == "smart_detail":
        detail_prompts = _build_detail_prompts(state)
        result["detail_prompts"] = detail_prompts
        result["prompts"] = detail_prompts

    elif generation_mode == "custom_assets":
        if include_detail_screens:
            detail_prompts = _build_detail_prompts(state)
            result["detail_prompts"] = detail_prompts
            result["prompts"] = detail_prompts
        else:
            result["detail_prompts"] = {}
            result["prompts"] = {}

    elif generation_mode == "hybrid":
        detail_prompts = _build_detail_prompts(state)
        result["detail_prompts"] = detail_prompts
        result["prompts"] = detail_prompts
        result["asset_prompts"] = _build_asset_prompts(state)

    return result
