from app.graph.state import ProductState


def ai_completion(state: ProductState) -> dict:
    merged = dict(state.get("merged_data", {}))
    missing = set(state.get("missing_fields", []))
    product_type = merged.get("product_type", {}).get("value") or "该产品"

    completed = dict(merged)
    if "brand" in missing:
        completed["brand"] = {"value": "未识别品牌", "source": "ai_inference", "confidence": 0.2}
    if "product_type" in missing:
        completed["product_type"] = {"value": "电商商品", "source": "ai_inference", "confidence": 0.25}
    if "selling_points" in missing:
        completed["selling_points"] = {
            "value": [f"{product_type}外观质感", "包装信息清晰", "适合电商详情页展示"],
            "source": "ai_inference",
            "confidence": 0.45,
        }
    if "target_audience" in missing:
        completed["target_audience"] = {
            "value": "关注品质、外观和购买确定性的电商用户",
            "source": "ai_inference",
            "confidence": 0.45,
        }

    return {"completed_data": completed}
