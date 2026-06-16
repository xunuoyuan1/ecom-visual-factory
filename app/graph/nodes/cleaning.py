from app.graph.state import ProductState


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def data_cleaning(state: ProductState) -> dict:
    source = state.get("completed_data") or state.get("merged_data", {})
    selling_points = _dedupe(list(source.get("selling_points", {}).get("value") or []))

    cleaned = {
        "brand": source.get("brand", {}),
        "product_type": source.get("product_type", {}),
        "specs": source.get("specs", {}),
        "selling_points": {
            "P1": selling_points[:1],
            "P2": selling_points[1:3],
            "P3": selling_points[3:],
        },
        "target_audience": source.get("target_audience", {}),
        "style_tags": source.get("style_tags", {"value": [], "source": "system", "confidence": 0.0}),
        "font_style": ["现代黑体", "高可读性中文标题"],
        "packaging_features": state.get("vision_data", {}).get("design_features", []),
        "confidence_cleaned": {
            "brand": source.get("brand", {}).get("confidence", 0),
            "product_type": source.get("product_type", {}).get("confidence", 0),
            "selling_points": source.get("selling_points", {}).get("confidence", 0),
        },
    }
    return {"cleaned_data": cleaned}
