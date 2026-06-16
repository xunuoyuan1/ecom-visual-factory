from app.graph.state import ProductState
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT


def prompt_generator(state: ProductState) -> dict:
    cleaned = state.get("cleaned_data", {})
    strategy = state.get("strategy", {})
    brand = cleaned.get("brand", {}).get("value") or "产品"
    product_type = cleaned.get("product_type", {}).get("value") or "商品"

    prompts = {}
    for screen_key, plan in strategy.items():
        title = f"{brand}{product_type}"
        subtitle = plan["core_selling_point"]
        prompts[screen_key] = (
            f"主标题：{title}\n"
            f"副标题：{subtitle}\n"
            f"屏幕目标：{plan['screen_goal']}\n"
            "布局说明：2:3竖版详情图，产品主体居中偏上，标题位于上方安全区，副标题靠近产品但不遮挡包装文字，底部保留留白用于转化信息。\n"
            "光影描述：柔和主光源，高级商业摄影质感，包装边缘清晰，避免过曝和阴影遮挡文字。\n"
            f"字体风格：{plan['font_style']}，中文排版清晰，字重有层级。\n"
            f"情绪风格：{plan['emotion']}。\n"
            f"视觉风格：{plan['visual_style']}。\n"
            f"禁止内容：{', '.join(plan['forbidden_content'])}。\n"
            f"{PRODUCT_FIDELITY_REQUIREMENT}"
        )
    return {"prompts": prompts}
