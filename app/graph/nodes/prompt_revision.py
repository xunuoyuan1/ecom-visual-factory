from app.graph.state import ProductState
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT, DETAIL_FIDELITY_REQUIREMENT


def prompt_revision(state: ProductState) -> dict:
    prompts = dict(state.get("prompts", {}))
    detail_prompts = dict(state.get("detail_prompts", {}))
    updated_detail = False

    for key, prompt in prompts.items():
        if PRODUCT_FIDELITY_REQUIREMENT not in prompt:
            prompts[key] = f"{prompt}\n{PRODUCT_FIDELITY_REQUIREMENT}"

    for key, prompt in detail_prompts.items():
        if DETAIL_FIDELITY_REQUIREMENT not in prompt:
            detail_prompts[key] = f"{prompt}\n{DETAIL_FIDELITY_REQUIREMENT}"
            updated_detail = True

    result: dict = {
        "prompts": prompts,
        "iteration": state.get("iteration", 0) + 1,
    }
    if updated_detail:
        result["detail_prompts"] = detail_prompts

    return result
