from app.graph.state import ProductState


def vision_product_parser(state: ProductState) -> dict:
    images = state.get("images", [])
    specs = state.get("user_specs", {})

    product_type = specs.get("product_type") or specs.get("category") or "未知品类"
    brand = specs.get("brand") or "未知品牌"

    return {
        "vision_data": {
            "raw_ocr": [],
            "visual_elements": [
                {"value": "产品主体居中", "confidence": 0.72, "source": "vision"},
                {"value": "包装正面可见", "confidence": 0.68, "source": "vision"},
            ],
            "packaging": {
                "brand": {"value": brand, "confidence": 0.55 if brand != "未知品牌" else 0.2, "source": "vision"},
                "product_type": {"value": product_type, "confidence": 0.6 if product_type != "未知品类" else 0.25, "source": "vision"},
                "image_count": {"value": len(images), "confidence": 1.0, "source": "system"},
            },
            "text_detected": [],
            "materials_guess": [],
            "design_features": [
                {"value": "保留原包装色彩与图案", "confidence": 0.75, "source": "vision"}
            ],
            "selling_signals": [],
            "user_guess": {},
            "confidence": {"overall": 0.62 if images else 0.1},
        }
    }
