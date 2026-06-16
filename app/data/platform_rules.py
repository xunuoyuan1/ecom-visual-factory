"""
Platform visual/image requirements for e-commerce detail pages.

Sources: Official seller documentation, platform style guides.
Entries with needs_manual_review=True require confirmation from official docs.
"""

ASSET_TYPES = [
    "主图",
    "使用场景图",
    "核心卖点图",
    "细节微距图",
    "尺寸参照图",
    "竞品对比图",
    "包装图",
    "广告摄影图",
    "7屏详情页",
]

PLATFORM_RULES = {
    "amazon": {
        "name": "Amazon",
        "needs_manual_review": False,
        "description": "全球最大电商平台，白底主图要求严格，支持 A+ 内容",
        "image_rules": {
            "主图": {
                "min_resolution": "1000x1000",
                "recommended": "3000x3000",
                "aspect_ratio": "1:1",
                "background": "纯白 (RGB 255,255,255)",
                "max_count": 1,
                "rules": ["产品占画面 85% 以上", "禁止文字、水印、LOGO", "禁止配件/装饰物", "服装类可有模特", "格式：JPEG/TIFF/PNG", "色彩模式：sRGB"],
            },
            "使用场景图": {"min_resolution": "1000x1000", "recommended": "3000x3000", "aspect_ratio": "1:1", "background": "场景环境", "max_count": 2, "rules": ["展示产品实际使用场景", "可有模特"]},
            "核心卖点图": {"min_resolution": "1000x1000", "recommended": "3000x3000", "aspect_ratio": "1:1", "background": "不限", "max_count": 3, "rules": ["可叠加文字标注卖点", "一图一卖点"]},
            "细节微距图": {"min_resolution": "1000x1000", "recommended": "3000x3000", "aspect_ratio": "1:1", "background": "不限", "max_count": 2, "rules": ["微距特写材质/工艺"]},
            "尺寸参照图": {"min_resolution": "1000x1000", "recommended": "3000x3000", "aspect_ratio": "1:1", "background": "不限", "max_count": 1, "rules": ["展示尺寸（含标注）"]},
            "竞品对比图": {"min_resolution": "1000x1000", "recommended": "3000x3000", "aspect_ratio": "1:1", "background": "不限", "max_count": 1, "rules": ["对比表格形式"]},
            "包装图": {"min_resolution": "1000x1000", "recommended": "3000x3000", "aspect_ratio": "1:1", "background": "不限", "max_count": 1, "rules": ["展示产品包装"]},
            "广告摄影图": {"min_resolution": "1200x628", "recommended": "1920x1080", "aspect_ratio": "16:9", "background": "场景环境", "max_count": 1, "rules": ["Spons Brands 广告", "清晰展示产品"]},
        },
        "detail_page_rules": {"min_images": 6, "max_images": 9, "preferred_format": "JPEG", "color_mode": "sRGB", "notes": "A+ 内容支持模块化排版"},
    },
    "tiktok_shop": {
        "name": "TikTok Shop",
        "needs_manual_review": True,
        "description": "短视频+直播电商，竖版内容优先，强调 UGC 真实感",
        "image_rules": {
            "主图": {"min_resolution": "750x1000", "recommended": "1500x2000", "aspect_ratio": "3:4", "background": "场景/纯白均可", "max_count": 1, "rules": ["产品占画面 60-80%", "可有简洁文字", "风格接近 UGC"]},
            "使用场景图": {"min_resolution": "750x1000", "recommended": "1500x2000", "aspect_ratio": "3:4", "background": "场景环境", "max_count": 3, "rules": ["真人使用场景优先", "生活方式感强"]},
            "核心卖点图": {"min_resolution": "750x1000", "recommended": "1500x2000", "aspect_ratio": "3:4", "background": "不限", "max_count": 2, "rules": ["卖点大字叠加", "简洁醒目"]},
            "细节微距图": {"min_resolution": "750x1000", "recommended": "1500x2000", "aspect_ratio": "3:4", "background": "不限", "max_count": 1},
            "尺寸参照图": {"min_resolution": "750x1000", "recommended": "1500x2000", "aspect_ratio": "3:4", "max_count": 1},
            "竞品对比图": {"min_resolution": "750x1000", "recommended": "1500x2000", "aspect_ratio": "3:4", "max_count": 1},
            "包装图": {"min_resolution": "750x1000", "recommended": "1500x2000", "aspect_ratio": "3:4", "max_count": 1},
            "广告摄影图": {"min_resolution": "1080x1080", "recommended": "1920x1920", "aspect_ratio": "1:1", "max_count": 1, "rules": ["TikTok 信息流广告", "竖版视频封面风"]},
        },
        "detail_page_rules": {"min_images": 6, "max_images": 10, "preferred_format": "JPEG/PNG", "video_priority": True, "notes": "TikTok 详情页建议配合短视频"},
    },
    "shopee": {
        "name": "Shopee",
        "needs_manual_review": True,
        "description": "东南亚及台湾领先电商，移动端为主，方图优先",
        "image_rules": {
            "主图": {"min_resolution": "500x500", "recommended": "1000x1000", "aspect_ratio": "1:1", "background": "纯白/浅色", "max_count": 1, "rules": ["产品占画面 70% 以上", "简洁干净"]},
            "使用场景图": {"min_resolution": "500x500", "recommended": "1000x1000", "aspect_ratio": "1:1", "max_count": 2},
            "核心卖点图": {"min_resolution": "500x500", "recommended": "1000x1000", "aspect_ratio": "1:1", "max_count": 2},
            "细节微距图": {"min_resolution": "500x500", "recommended": "1000x1000", "aspect_ratio": "1:1", "max_count": 1},
            "尺寸参照图": {"min_resolution": "500x500", "recommended": "1000x1000", "aspect_ratio": "1:1", "max_count": 1},
            "竞品对比图": {"min_resolution": "500x500", "recommended": "1000x1000", "aspect_ratio": "1:1", "max_count": 1},
            "包装图": {"min_resolution": "500x500", "recommended": "1000x1000", "aspect_ratio": "1:1", "max_count": 1},
            "广告摄影图": {"max_count": 1},
        },
        "detail_page_rules": {"min_images": 3, "max_images": 9, "preferred_format": "JPEG/PNG", "notes": "手机端单列瀑布流显示"},
    },
    "temu": {
        "name": "Temu",
        "needs_manual_review": True,
        "description": "拼多多海外版，极致性价比定位",
        "image_rules": {
            "主图": {"min_resolution": "600x600", "recommended": "1200x1200", "aspect_ratio": "1:1", "background": "纯白/浅色", "max_count": 1, "rules": ["产品清晰展示", "可标注价格"]},
            "使用场景图": {"min_resolution": "600x600", "recommended": "1200x1200", "aspect_ratio": "1:1", "max_count": 3, "rules": ["突出实用价值", "可与同类对比"]},
            "核心卖点图": {"min_resolution": "600x600", "recommended": "1200x1200", "aspect_ratio": "1:1", "max_count": 2},
            "细节微距图": {"min_resolution": "600x600", "recommended": "1200x1200", "aspect_ratio": "1:1", "max_count": 1},
            "尺寸参照图": {"max_count": 1},
            "竞品对比图": {"max_count": 1},
            "包装图": {"max_count": 1},
            "广告摄影图": {"max_count": 1},
        },
        "detail_page_rules": {"min_images": 5, "max_images": 15, "preferred_format": "JPEG/PNG", "notes": "强调性价比"},
    },
    "lazada": {
        "name": "Lazada (LazMall)",
        "needs_manual_review": True,
        "description": "东南亚六国覆盖，宽高比灵活支持 1:1/3:4",
        "image_rules": {
            "主图": {"min_resolution": "800x800", "recommended": "1200x1200", "aspect_ratio": "1:1", "background": "纯白", "max_count": 1, "rules": ["产品占 70% 以上", "纯白背景", "无水印/LOGO"]},
            "使用场景图": {"aspect_ratio": "4:3", "max_count": 2},
            "核心卖点图": {"max_count": 2},
            "细节微距图": {"max_count": 1},
            "尺寸参照图": {"max_count": 1},
            "竞品对比图": {"max_count": 1},
            "包装图": {"max_count": 1},
            "广告摄影图": {"max_count": 1},
        },
        "detail_page_rules": {"min_images": 3, "max_images": 8, "preferred_format": "JPEG/PNG"},
    },
    "jd": {
        "name": "京东",
        "needs_manual_review": True,
        "description": "中国 B2C 品质电商，白底主图严格，支持 3D 展示",
        "image_rules": {
            "主图": {"min_resolution": "800x800", "recommended": "1200x1200", "aspect_ratio": "1:1", "background": "纯白 (RGB 255,255,255)", "max_count": 1, "rules": ["产品占 70% 以上", "纯白背景", "禁止文字覆盖产品"]},
            "使用场景图": {"max_count": 2, "background": "场景环境"},
            "核心卖点图": {"max_count": 2, "rules": ["可叠加文字说明"]},
            "细节微距图": {"max_count": 1},
            "尺寸参照图": {"max_count": 1},
            "竞品对比图": {"max_count": 1},
            "包装图": {"max_count": 1},
            "广告摄影图": {"max_count": 1},
        },
        "detail_page_rules": {"min_images": 5, "max_images": 10, "preferred_format": "JPEG/PNG", "notes": "支持 3D/360 度展示"},
    },
    "taobao": {
        "name": "淘宝",
        "needs_manual_review": True,
        "description": "中国最大 C2C 电商，5张主图+详情页长图模式",
        "image_rules": {
            "主图": {"min_resolution": "800x800", "recommended": "1200x1200", "aspect_ratio": "1:1", "background": "纯白优先", "max_count": 1, "rules": ["第一张纯白", "后四张场景/卖点/细节", "不强制无文字"]},
            "使用场景图": {"max_count": 2},
            "核心卖点图": {"max_count": 2},
            "细节微距图": {"max_count": 1},
            "尺寸参照图": {"max_count": 1},
            "竞品对比图": {"max_count": 1},
            "包装图": {"max_count": 1},
            "广告摄影图": {"max_count": 1},
        },
        "detail_page_rules": {"min_images": 0, "max_images": 50, "preferred_format": "JPEG/PNG", "notes": "详情页为长图拼接，手机端宽 750px", "detail_page_width": 750},
    },
    "tmall": {
        "name": "天猫",
        "needs_manual_review": True,
        "description": "天猫 B2C，主图规范严格，详情页宽 790px",
        "image_rules": {
            "主图": {"min_resolution": "800x800", "recommended": "1200x1200", "aspect_ratio": "1:1", "background": "纯白", "max_count": 1, "rules": ["第一张强制纯白", "后四张可场景/细节"]},
            "使用场景图": {"max_count": 2},
            "核心卖点图": {"max_count": 2},
            "细节微距图": {"max_count": 1},
            "尺寸参照图": {"max_count": 1},
            "竞品对比图": {"max_count": 1},
            "包装图": {"max_count": 1},
            "广告摄影图": {"max_count": 1},
        },
        "detail_page_rules": {"min_images": 0, "max_images": 50, "preferred_format": "JPEG/PNG", "detail_page_width": 790, "notes": "无线端详情页宽度 790px"},
    },
    "alibaba": {
        "name": "阿里国际站",
        "needs_manual_review": True,
        "description": "全球 B2B 批发平台，强调产品参数和公司资质",
        "image_rules": {
            "主图": {"min_resolution": "640x640", "recommended": "1000x1000", "aspect_ratio": "1:1", "background": "纯白", "max_count": 1, "rules": ["产品清晰展示", "可有简洁标题/参数"]},
            "使用场景图": {"max_count": 2},
            "核心卖点图": {"max_count": 3, "rules": ["B2B 卖点（价格/交期/MOQ）"]},
            "细节微距图": {"max_count": 2},
            "尺寸参照图": {"max_count": 1, "rules": ["标注精确尺寸参数"]},
            "竞品对比图": {"max_count": 1},
            "包装图": {"max_count": 1, "rules": ["侧重运输包装"]},
            "广告摄影图": {"max_count": 1},
        },
        "detail_page_rules": {"min_images": 3, "max_images": 8, "notes": "B2B 侧重产品参数表和公司信息"},
    },
}


def get_platform_rules(platform: str) -> dict | None:
    """Get rules for a specific platform by its key."""
    return PLATFORM_RULES.get(platform)


def get_asset_type_info(asset_type: str) -> dict:
    """Get default info for an asset type across all platforms."""
    for rules in PLATFORM_RULES.values():
        if asset_type in rules.get("image_rules", {}):
            return rules["image_rules"][asset_type]
    return {"max_count": 1}
