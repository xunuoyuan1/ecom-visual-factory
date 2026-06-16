from typing import Any

from app.graph.nodes.completion import ai_completion
from app.graph.nodes.image_generation import image_generation
from app.graph.nodes.prompt_revision import prompt_revision
from app.graph.nodes.qa import qa_inspector, should_revise
from app.graph.nodes.strategy import visual_strategy
from app.graph.nodes.web import web_enhancement
from app.graph.nodes.cleaning import data_cleaning
from app.graph.nodes.merge import data_merge_and_completeness, route_selector
from app.graph.nodes.prompt_generator import prompt_generator
from app.graph.nodes.validator import input_validator
from app.graph.nodes.vision import vision_product_parser
from app.graph.nodes.asset_planning import asset_planning  # NEW
from app.graph.state import ProductState


class SimpleGraphRunner:
    """Fallback runner for local tests when LangGraph is not installed."""

    def invoke(self, state: ProductState) -> ProductState:
        state.update(input_validator(state))
        state.update(vision_product_parser(state))
        state.update(data_merge_and_completeness(state))
        if route_selector(state) == "completion":
            state.update(ai_completion(state))
        state.update(data_cleaning(state))
        state.update(web_enhancement(state))
        state.update(visual_strategy(state))
        state.update(asset_planning(state))  # NEW
        state.update(prompt_generator(state))
        state.update(image_generation(state))
        state.update(qa_inspector(state))
        if should_revise(state) == "revise":
            state.update(prompt_revision(state))
            state.update(image_generation(state))
            state.update(qa_inspector(state))
        return state


def build_graph() -> Any:
    return SimpleGraphRunner()
