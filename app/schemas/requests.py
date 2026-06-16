from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.graph.state import ProductState


class GenerateConstraints(BaseModel):
    platform: str = "tmall"
    aspect_ratio: str = "2:3"
    screens: int = 7
    enable_image_generation: bool = False
    enable_web_enhancement: bool = True
    max_qa_iterations: int = 1
    text_only_mode: bool = False


class GenerateRequest(BaseModel):
    sku_id: str = Field(default_factory=lambda: f"SKU-{uuid4().hex[:8]}")
    images: list[str] = Field(default_factory=list)
    specs: dict[str, Any] = Field(default_factory=dict)
    selling_points: list[str] = Field(default_factory=list)
    constraints: GenerateConstraints = Field(default_factory=GenerateConstraints)

    def to_state(self) -> ProductState:
        return {
            "job_id": uuid4().hex,
            "sku_id": self.sku_id,
            "images": self.images,
            "user_specs": self.specs,
            "user_selling_points": self.selling_points,
            "user_constraints": self.constraints.model_dump(),
            "iteration": 0,
            "errors": [],
        }


class BatchGenerateRequest(BaseModel):
    items: list[GenerateRequest]
