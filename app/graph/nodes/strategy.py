from app.graph.state import ProductState
from app.prompts.constants import SCREEN_FLOW


def visual_strategy(state: ProductState) -> dict:
    cleaned = state.get("cleaned_data", {})
    points = cleaned.get("selling_points", {})
    p1 = points.get("P1") or ["产品核心价值"]
    p2 = points.get("P2") or ["细节品质", "使用理由"]
    p3 = points.get("P3") or ["购买确定性"]

    selling_by_screen = {
        "screen_1": p1[0],
        "screen_2": p2[0] if p2 else p1[0],
        "screen_3": "包装真实还原与品质细节",
        "screen_4": p2[1] if len(p2) > 1 else "规格与结构说明",
        "screen_5": "目标用户使用场景",
        "screen_6": p3[0] if p3 else "细节对比与风险消除",
        "screen_7": "购买理由总结",
    }

    strategy = {}
    for key, (stage, goal) in SCREEN_FLOW.items():
        strategy[key] = {
            "screen_goal": f"{stage}：{goal}",
            "core_selling_point": selling_by_screen[key],
            "forbidden_content": ["虚构认证", "修改LOGO", "编造包装文字", "夸大功效"],
            "visual_style": "干净电商详情页，高质感产品摄影，统一品牌色",
            "font_style": "现代黑体，标题醒目，副标题清晰",
            "emotion": "可信、清晰、有购买确定性",
        }
    return {"strategy": strategy}
