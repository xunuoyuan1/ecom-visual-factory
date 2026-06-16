from typing import Any, Literal, TypedDict

Source = Literal["user_input", "vision", "web_industry", "ai_inference", "system"]


class ProductState(TypedDict, total=False):
    job_id: str
    sku_id: str
    product_name: str
    brand: str
    product_type: str
    target_market: str
    target_audience: str

    images: list[str]
    image_roles: list[str]
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

    # Generation mode
    generation_mode: str
    include_detail_screens: bool

    # Asset planning
    asset_types_requested: list[dict[str, Any]]
    platform_rules_applied: dict[str, Any]
    asset_plan: list[dict[str, Any]]
    asset_prompts: dict[str, list[str]]

    # Detail prompts (separate from asset_prompts)
    detail_prompts: dict[str, str]

    # Existing (backward compat, populated from detail_prompts for detail screen modes)
    prompts: dict[str, str]
    generated_images: dict[str, str]
    image_generation_status: dict[str, Any]
    qa_report: dict[str, Any]

    vision_mode_used: str
    llm_mode_used: str

    iteration: int
    errors: list[dict[str, Any]]
