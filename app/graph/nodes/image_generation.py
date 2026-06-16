from app.graph.state import ProductState


def image_generation(state: ProductState) -> dict:
    constraints = state.get("user_constraints", {})
    prompts = state.get("prompts", {})

    if not constraints.get("enable_image_generation", False):
        return {
            "generated_images": {},
            "image_generation_status": {
                "enabled": False,
                "message": "Image generation is disabled for the MVP test flow.",
            },
        }

    return {
        "generated_images": {key: "" for key in prompts},
        "image_generation_status": {
            "enabled": True,
            "message": "Image generation adapter is not connected yet.",
        },
    }
