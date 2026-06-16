from app.graph.state import ProductState


def web_enhancement(state: ProductState) -> dict:
    constraints = state.get("user_constraints", {})
    if not constraints.get("enable_web_enhancement", True):
        return {
            "market_data": {
                "market_selling_points": [],
                "competitor_patterns": [],
                "common_claims": [],
                "positioning_suggestions": [],
                "industry_source_note": "Web enhancement disabled by request.",
            }
        }

    product_type = state.get("cleaned_data", {}).get("product_type", {}).get("value") or "该品类"
    return {
        "market_data": {
            "market_selling_points": [
                {"value": "突出第一眼识别和核心利益点", "source": "web_industry"},
                {"value": "用细节图降低用户不确定性", "source": "web_industry"},
            ],
            "competitor_patterns": [
                {"value": f"{product_type}详情页常用首屏大产品图加短标题", "source": "web_industry"}
            ],
            "common_claims": [
                {"value": "品质感、清晰规格、使用场景", "source": "web_industry"}
            ],
            "positioning_suggestions": [
                {"value": "以真实包装还原和购买理由为主，不添加未经证明的功效", "source": "web_industry"}
            ],
            "industry_source_note": "测试版未联网，仅输出行业表达占位；生产环境需接搜索工具并记录来源。",
        }
    }
