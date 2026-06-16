from typing import Any, Literal, TypedDict


Source = Literal["user_input", "vision", "web_industry", "ai_inference", "system"]


class ProductState(TypedDict, total=False):
    job_id: str
    sku_id: str

    images: list[str]
    user_specs: dict[str, Any]
    user_selling_points: list[str]
    user_constraints: dict[str, Any]

    completeness_score: int
    missing_fields: list[str]
    route: Literal["direct", "completion"]

    vision_data: dict[str, Any]
    merged_data: dict[str, Any]
    completed_data: dict[str, Any]
    cleaned_data: dict[str, Any]
    market_data: dict[str, Any]
    strategy: dict[str, Any]

    prompts: dict[str, str]
    generated_images: dict[str, str]
    image_generation_status: dict[str, Any]
    qa_report: dict[str, Any]

    iteration: int
    errors: list[dict[str, Any]]
