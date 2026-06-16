from app.graph.state import ProductState
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT, DETAIL_FIDELITY_REQUIREMENT


def qa_inspector(state: ProductState) -> dict:
    generation_mode = state.get("generation_mode", "smart_detail")
    include_detail_screens = state.get("include_detail_screens", False)

    high = []
    medium = []

    if generation_mode == "smart_detail":
        # Validate detail_prompts (or legacy prompts) — 7 screens with fidelity
        prompts = state.get("detail_prompts", {}) or state.get("prompts", {})
        if len(prompts) != 7:
            high.append("Detail prompt数量不是7屏。")
        for key, prompt in prompts.items():
            if DETAIL_FIDELITY_REQUIREMENT not in prompt:
                high.append(f"{key} 缺少产品保真硬性要求。")
            if "主标题：" not in prompt or "副标题：" not in prompt:
                medium.append(f"{key} 缺少主标题或副标题。")

    elif generation_mode == "custom_assets":
        # Validate asset_prompts
        asset_prompts = state.get("asset_prompts", {})
        if not asset_prompts:
            high.append("Asset prompts 为空。")
        else:
            for asset_type, prompts_list in asset_prompts.items():
                if not prompts_list:
                    medium.append(f"{asset_type} 的 prompts 为空。")

        if include_detail_screens:
            # Also validate detail prompts
            detail_prompts = state.get("detail_prompts", {}) or state.get("prompts", {})
            if len(detail_prompts) != 7:
                high.append("Detail prompt数量不是7屏。")
            for key, prompt in detail_prompts.items():
                if DETAIL_FIDELITY_REQUIREMENT not in prompt:
                    high.append(f"{key} 缺少产品保真硬性要求。")

    elif generation_mode == "hybrid":
        # Validate both detail_prompts and asset_prompts
        # Detail prompts
        detail_prompts = state.get("detail_prompts", {}) or state.get("prompts", {})
        if len(detail_prompts) != 7:
            high.append("Detail prompt数量不是7屏。")
        for key, prompt in detail_prompts.items():
            if DETAIL_FIDELITY_REQUIREMENT not in prompt:
                high.append(f"{key} 缺少产品保真硬性要求。")
            if "主标题：" not in prompt or "副标题：" not in prompt:
                medium.append(f"{key} 缺少主标题或副标题。")

        # Asset prompts
        asset_prompts = state.get("asset_prompts", {})
        if not asset_prompts:
            high.append("Asset prompts 为空。")
        else:
            for asset_type, prompts_list in asset_prompts.items():
                if not prompts_list:
                    medium.append(f"{asset_type} 的 prompts 为空。")

    else:
        # Unknown mode — validate prompts generically
        prompts = state.get("prompts", {})
        if prompts and len(prompts) != 7:
            high.append("Prompt数量不是7屏。")
        for key, prompt in prompts.items():
            if PRODUCT_FIDELITY_REQUIREMENT not in prompt:
                high.append(f"{key} 缺少产品保真硬性要求。")

    passed = not high
    return {
        "qa_report": {
            "pass": passed,
            "issues": high + medium,
            "severity": {"high": high, "medium": medium, "low": []},
            "fix_suggestions": ["补齐缺失硬性约束并重新生成 Prompt。"] if high else [],
        },
    }


def should_revise(state: ProductState) -> str:
    qa_report = state.get("qa_report", {})
    high = qa_report.get("severity", {}).get("high", [])
    max_iterations = state.get("user_constraints", {}).get("max_qa_iterations", 1)
    if high and state.get("iteration", 0) < max_iterations:
        return "revise"
    return "end"
