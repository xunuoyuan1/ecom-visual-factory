from app.graph.state import ProductState


SCREEN_PRODUCT_KEYWORDS = (
    "智能手表",
    "手表",
    "运动手表",
    "电子表",
    "smartwatch",
    "watch",
    "屏幕",
    "触控",
    "显示屏",
)

CREATIVE_ASSET_TYPES = ("使用场景图", "广告摄影图", "核心卖点图")


def is_screen_product(state: ProductState) -> bool:
    values = [
        state.get("product_name", ""),
        state.get("product_type", ""),
        str(state.get("user_specs", {})),
        " ".join(state.get("user_selling_points", [])),
    ]
    text = " ".join(values).lower()
    return any(keyword.lower() in text for keyword in SCREEN_PRODUCT_KEYWORDS)


def screen_ui_guidance(state: ProductState, asset_type: str) -> str:
    if not is_screen_product(state):
        return ""

    base = (
        "屏幕显示策略：产品屏幕必须点亮，显示通用非品牌化运动健康仪表盘 UI，"
        "可包含时间、步数、心率趋势线、运动记录、消息提醒等轻量图标；"
        "UI 现代清晰，不遮挡圆角矩形屏幕结构；不得出现 Apple、Apple Watch、任何品牌 Logo，"
        "不得出现医疗诊断、FDA、clinical、100% accurate、血压精确诊断等暗示。"
    )

    if asset_type == "主图":
        return (
            base
            + " 主图创意边界：仍保持 Amazon 合规白底、1:1、无外加文字和无装饰物，"
            "但使用更高级的棚拍高光、轻微 3/4 角度和屏幕微反光，避免死板黑屏。"
        )

    if asset_type in CREATIVE_ASSET_TYPES:
        return (
            base
            + " 创意方向：允许更有生活方式和科技感的构图，例如健身、通勤、桌面晨间、轻户外场景；"
            "画面要有明确光影层次、真实人物动作或环境氛围，但不添加夸张营销大字。"
        )

    return base


def enhance_asset_prompt(state: ProductState, asset_type: str, prompt: str) -> str:
    guidance = screen_ui_guidance(state, asset_type)
    if not guidance:
        return prompt
    return f"{prompt} {guidance}"
