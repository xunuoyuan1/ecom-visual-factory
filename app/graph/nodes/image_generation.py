from app.graph.state import ProductState


def image_generation(state: ProductState) -> dict:
    constraints = state.get("user_constraints", {})
    detail_prompts = state.get("detail_prompts", {}) or state.get("prompts", {})
    asset_prompts = state.get("asset_prompts", {})

    if not constraints.get("enable_image_generation", False):
        return {
            "generated_images": {},
            "image_generation_status": {
                "enabled": False,
                "message": "Image generation is disabled for the MVP test flow.",
            },
        }

    generated_images = {f"detail:{key}": "" for key in detail_prompts}
    for asset_type, prompts in asset_prompts.items():
        for index, _prompt in enumerate(prompts, start=1):
            generated_images[f"asset:{asset_type}:{index}"] = ""

    return {
        "generated_images": generated_images,
        "image_generation_status": {
            "enabled": True,
            "message": "Image generation adapter is not connected yet.",
        },
    }
