from app.graph.state import ProductState
from app.prompts.constants import PRODUCT_FIDELITY_REQUIREMENT


def qa_inspector(state: ProductState) -> dict:
    prompts = state.get("prompts", {})
    high = []
    medium = []

    if len(prompts) != 7:
        high.append("Prompt数量不是7屏。")

    for key, prompt in prompts.items():
        if PRODUCT_FIDELITY_REQUIREMENT not in prompt:
            high.append(f"{key} 缺少产品保真硬性要求。")
        if "画面比例为2:3竖版" not in prompt:
            high.append(f"{key} 缺少2:3竖版比例要求。")
        if "主标题：" not in prompt or "副标题：" not in prompt:
            medium.append(f"{key} 缺少主标题或副标题。")

    passed = not high
    return {
        "qa_report": {
            "pass": passed,
            "issues": high + medium,
            "severity": {"high": high, "medium": medium, "low": []},
            "fix_suggestions": ["补齐缺失硬性约束并重新生成 Prompt。"] if high else [],
        }
    }


def should_revise(state: ProductState) -> str:
    qa_report = state.get("qa_report", {})
    high = qa_report.get("severity", {}).get("high", [])
    max_iterations = state.get("user_constraints", {}).get("max_qa_iterations", 1)
    if high and state.get("iteration", 0) < max_iterations:
        return "revise"
    return "end"
