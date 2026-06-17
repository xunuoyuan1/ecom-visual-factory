"""Asset planning node - generates structured asset plans from product info + platform rules."""

from app.data.platform_rules import PLATFORM_RULES, ASSET_TYPES
from app.graph.state import ProductState
from app.prompts.enhancers import enhance_asset_prompt


def asset_planning(state: ProductState) -> dict:
    """
    Generate structured asset plan based on:
    - Generation mode (smart_detail skips asset planning)
    - User-requested asset types and counts
    - Platform image rules
    - Product information

    Outputs:
    - platform_rules_applied: the full platform rule set
    - asset_plan: list of planned assets with specs
    - asset_prompts: mock prompts per asset type
    """
    generation_mode = state.get("generation_mode", "smart_detail")

    # smart_detail mode: skip asset planning entirely, return empty
    if generation_mode == "smart_detail":
        return {
            "platform_rules_applied": {},
            "asset_plan": [],
            "asset_prompts": {},
        }

    # custom_assets or hybrid: proceed with full asset planning
    platform_key = (
        state.get("user_constraints", {})
        .get("platform", "tmall")
        .lower()
        .replace(" ", "_")
    )

    # Map common platform names
    platform_map = {
        "amazon": "amazon",
        "tiktok shop": "tiktok_shop",
        "tiktokshop": "tiktok_shop",
        "shopee": "shopee",
        "temu": "temu",
        "lazada": "lazada",
        "jd": "jd",
        "京东": "jd",
        "taobao": "taobao",
        "淘宝": "taobao",
        "tmall": "tmall",
        "天猫": "tmall",
        "alibaba": "alibaba",
        "阿里国际站": "alibaba",
    }
    platform_key = platform_map.get(platform_key, platform_key)
    platform_rules = PLATFORM_RULES.get(platform_key, {})

    # Get user-requested asset types (or default to all types)
    requested_types = state.get("asset_types_requested", [])
    if not requested_types:
        # Default: one of each
        requested_types = [{"type_name": t, "count": 1} for t in ASSET_TYPES]

    # Build asset_plan
    asset_plan = []
    image_rules = platform_rules.get("image_rules", {})
    detail_rules = platform_rules.get("detail_page_rules", {})

    for req in requested_types:
        type_name = req["type_name"]
        count = int(req.get("count", 1))

        if type_name == "7屏详情页":
            # Special: 7-screen detail page uses the existing prompts field
            asset_plan.append({
                "type": "7屏详情页",
                "count": 1,
                "platform_rule": {
                    "min_images": detail_rules.get("min_images", 0),
                    "max_images": detail_rules.get("max_images", 10),
                    "notes": detail_rules.get("notes", ""),
                },
                "prompt_generated": True,
            })
            continue

        # Look up platform rules for this asset type
        type_rules = image_rules.get(type_name, {})
        actual_count = min(count, type_rules.get("max_count", 999))

        asset_plan.append({
            "type": type_name,
            "count": actual_count,
            "min_resolution": type_rules.get("min_resolution", "800x800"),
            "recommended_resolution": type_rules.get("recommended", "1200x1200"),
            "aspect_ratio": type_rules.get("aspect_ratio", "1:1"),
            "background": type_rules.get("background", "不限"),
            "rules": type_rules.get("rules", []),
        })

    # Generate mock asset_prompts
    asset_prompts = {}
    output_language = state.get("output_language") or "中文"
    for item in asset_plan:
        t = item["type"]
        if t == "7屏详情页":
            continue  # Uses existing prompts field
        c = item.get("count", 1)
        asset_prompts[t] = [
            enhance_asset_prompt(
                state,
                t,
                f"[{t}] ({platform_rules.get('name', platform_key)}) "
                f"{item.get('recommended_resolution', '高分辨率')} "
                f"{item.get('aspect_ratio', '1:1')} "
                f"画面文字语言：{output_language}，所有可见文字必须使用该语言。"
                f"产品描述：{state.get('product_name', '待填产品')} - 第{n+1}张",
            )
            for n in range(c)
        ]

    return {
        "platform_rules_applied": platform_rules,
        "asset_plan": asset_plan,
        "asset_prompts": asset_prompts,
    }
