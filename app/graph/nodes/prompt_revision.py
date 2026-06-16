from app.graph.state import ProductState
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT


def prompt_revision(state: ProductState) -> dict:
    prompts = dict(state.get("prompts", {}))
    for key, prompt in prompts.items():
        if PRODUCT_FIDELITY_REQUIREMENT not in prompt:
            prompts[key] = f"{prompt}\n{PRODUCT_FIDELITY_REQUIREMENT}"

    return {
        "prompts": prompts,
        "iteration": state.get("iteration", 0) + 1,
    }
