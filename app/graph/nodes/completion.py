from app.graph.state import ProductState
from app.services import llm


def _mock_completion(state: ProductState) -> dict:
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


def ai_completion(state: ProductState) -> dict:
    if llm.should_use_live_llm():
        try:
            return {"completed_data": llm.complete_product_data(state), "llm_mode_used": "live"}
        except llm.LLMServiceError as exc:
            errors = list(state.get("errors", []))
            errors.append({"node": "completion", "severity": "medium", "message": str(exc)})
            result = _mock_completion(state)
            result["errors"] = errors
            result["llm_mode_used"] = "mock_fallback"
            return result

    return _mock_completion(state)
