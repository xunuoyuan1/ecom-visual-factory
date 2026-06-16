from app.graph.state import ProductState


def input_validator(state: ProductState) -> dict:
    errors = list(state.get("errors", []))
    constraints = state.get("user_constraints", {})
    images = state.get("images", [])

    if not images and not constraints.get("text_only_mode", False):
        errors.append(
            {
                "node": "validator",
                "severity": "high",
                "message": "At least one product image is required unless text_only_mode is enabled.",
            }
        )

    if constraints.get("screens", 7) != 7:
        errors.append(
            {
                "node": "validator",
                "severity": "medium",
                "message": "The MVP is optimized for exactly 7 detail screens.",
            }
        )

    return {"errors": errors}
