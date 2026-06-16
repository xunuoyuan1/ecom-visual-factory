from typing import Any

from app.graph.state import ProductState


REQUIRED_FIELDS = ("brand", "product_type", "selling_points", "target_audience")


def _field(value: Any, source: str, confidence: float) -> dict[str, Any]:
    return {"value": value, "source": source, "confidence": confidence}


def data_merge_and_completeness(state: ProductState) -> dict:
    specs = state.get("user_specs", {})
    vision = state.get("vision_data", {})
    packaging = vision.get("packaging", {})
    selling_points = state.get("user_selling_points", [])

    brand = specs.get("brand") or packaging.get("brand", {}).get("value") or ""
    product_type = specs.get("product_type") or specs.get("category") or packaging.get("product_type", {}).get("value") or ""

    merged = {
        "brand": _field(brand, "user_input" if specs.get("brand") else "vision", 0.95 if specs.get("brand") else 0.55),
        "product_type": _field(
            product_type,
            "user_input" if specs.get("product_type") or specs.get("category") else "vision",
            0.95 if specs.get("product_type") or specs.get("category") else 0.6,
        ),
        "specs": _field(specs, "user_input", 0.9 if specs else 0.0),
        "selling_points": _field(selling_points, "user_input", 0.95 if selling_points else 0.0),
        "target_audience": _field(specs.get("target_audience", ""), "user_input", 0.85 if specs.get("target_audience") else 0.0),
        "style_tags": _field(specs.get("style_tags", []), "user_input", 0.8 if specs.get("style_tags") else 0.0),
    }

    score = 0
    if len(state.get("images", [])) >= 1:
        score += 25
    if len(state.get("images", [])) >= 3:
        score += 15
    if brand and brand != "未知品牌":
        score += 15
    if product_type and product_type != "未知品类":
        score += 15
    if specs:
        score += 15
    if len(selling_points) >= 3:
        score += 15

    missing = []
    if not brand or brand == "未知品牌":
        missing.append("brand")
    if not product_type or product_type == "未知品类":
        missing.append("product_type")
    if len(selling_points) < 3:
        missing.append("selling_points")
    if not specs.get("target_audience"):
        missing.append("target_audience")

    route = "direct" if score >= 80 and not missing else "completion"
    return {
        "merged_data": merged,
        "completeness_score": score,
        "missing_fields": missing,
        "route": route,
    }


def route_selector(state: ProductState) -> str:
    return state.get("route", "completion")
