from app.graph.state import ProductState
from app.config import settings
from app.services import llm


def _targets_enabled() -> set[str]:
    return {
        item.strip().lower()
        for item in settings.image_generation_targets.split(",")
        if item.strip()
    }


def _collect_image_tasks(state: ProductState) -> list[dict]:
    targets = _targets_enabled()
    tasks = []

    if "detail" in targets:
        detail_prompts = state.get("detail_prompts", {}) or state.get("prompts", {})
        for key, prompt in detail_prompts.items():
            tasks.append({"id": f"detail:{key}", "type": "detail", "prompt": prompt})

    if "asset" in targets:
        asset_prompts = state.get("asset_prompts", {})
        for asset_type, prompts in asset_prompts.items():
            for index, prompt in enumerate(prompts, start=1):
                tasks.append(
                    {
                        "id": f"asset:{asset_type}:{index}",
                        "type": "asset",
                        "asset_type": asset_type,
                        "prompt": prompt,
                    }
                )

    return tasks[: max(settings.max_images_per_request, 0)]


def image_generation(state: ProductState) -> dict:
    constraints = state.get("user_constraints", {})
    tasks = _collect_image_tasks(state)

    if not constraints.get("enable_image_generation", False):
        return {
            "generated_images": {},
            "image_generation_status": {
                "enabled": False,
                "message": "Image generation is disabled for the MVP test flow.",
                "planned_count": len(tasks),
                "max_images_per_request": settings.max_images_per_request,
            },
        }

    if not llm.should_use_live_llm():
        return {
            "generated_images": {
                task["id"]: {
                    "id": task["id"],
                    "type": task["type"],
                    "prompt": task["prompt"],
                    "b64_json": None,
                    "url": None,
                    "error": "Image generation requires LLM_MODE=live and OPENAI_API_KEY.",
                }
                for task in tasks
            },
            "image_generation_status": {
                "enabled": True,
                "mode": "mock_fallback",
                "message": "Image generation was requested but live OpenAI credentials are not active.",
                "requested_count": len(tasks),
                "generated_count": 0,
                "max_images_per_request": settings.max_images_per_request,
            },
        }

    generated_images = {}
    errors = list(state.get("errors", []))
    generated_count = 0
    for task in tasks:
        try:
            generated_images[task["id"]] = llm.generate_image(
                task["prompt"],
                image_id=task["id"],
                image_type=task["type"],
            )
            generated_count += 1
        except llm.LLMServiceError as exc:
            message = str(exc)
            errors.append({"node": "image_generation", "severity": "medium", "message": message})
            generated_images[task["id"]] = {
                "id": task["id"],
                "type": task["type"],
                "prompt": task["prompt"],
                "b64_json": None,
                "url": None,
                "error": message,
            }

    status = {
        "enabled": True,
        "mode": "live",
        "message": "Image generation completed." if generated_count else "Image generation completed with no images.",
        "requested_count": len(tasks),
        "generated_count": generated_count,
        "max_images_per_request": settings.max_images_per_request,
        "targets": sorted(_targets_enabled()),
    }
    result = {
        "generated_images": generated_images,
        "image_generation_status": status,
    }
    if errors != state.get("errors", []):
        result["errors"] = errors
    return {
        **result,
    }
