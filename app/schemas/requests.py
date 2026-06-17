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
    generation_mode: str = "smart_detail"
    include_detail_screens: bool = False


class AssetTypeConfig(BaseModel):
    type_name: str
    count: int = 1


class GenerateRequest(BaseModel):
    product_name: str = ""
    brand: str = ""
    product_type: str = ""
    target_market: str = "中国大陆"
    output_language: str = ""
    target_audience: str = ""
    sku_id: str = Field(default_factory=lambda: f"SKU-{uuid4().hex[:8]}")
    images: list[str] = Field(default_factory=list)
    image_roles: list[str] = Field(default_factory=list)
    specs: dict[str, Any] = Field(default_factory=dict)
    selling_points: list[str] = Field(default_factory=list)
    asset_types: list[AssetTypeConfig] = Field(default_factory=list)
    constraints: GenerateConstraints = Field(default_factory=GenerateConstraints)

    def to_state(self) -> ProductState:
        user_specs = dict(self.specs)
        if self.brand:
            user_specs.setdefault("brand", self.brand)
        if self.product_type:
            user_specs.setdefault("product_type", self.product_type)
        if self.target_audience:
            user_specs.setdefault("target_audience", self.target_audience)
        if self.product_name:
            user_specs.setdefault("product_name", self.product_name)
        if self.target_market:
            user_specs.setdefault("target_market", self.target_market)
        output_language = self.output_language or infer_default_language(self.target_market)
        if output_language:
            user_specs.setdefault("output_language", output_language)

        return {
            "job_id": uuid4().hex,
            "sku_id": self.sku_id,
            "product_name": self.product_name,
            "brand": self.brand,
            "product_type": self.product_type,
            "target_market": self.target_market,
            "output_language": output_language,
            "target_audience": self.target_audience,
            "images": self.images,
            "image_roles": self.image_roles,
            "user_specs": user_specs,
            "user_selling_points": self.selling_points,
            "asset_types_requested": [
                {"type_name": a.type_name, "count": a.count}
                for a in self.asset_types
            ],
            "user_constraints": self.constraints.model_dump(),
            "generation_mode": self.constraints.generation_mode,
            "include_detail_screens": self.constraints.include_detail_screens,
            "iteration": 0,
            "errors": [],
        }


class BatchGenerateRequest(BaseModel):
    items: list[GenerateRequest]


def infer_default_language(target_market: str) -> str:
    mapping = {
        "美国": "English",
        "欧洲": "English",
        "日韩": "Japanese",
        "日本": "Japanese",
        "韩国": "Korean",
        "东南亚": "English",
        "南美": "Spanish",
        "拉美": "Spanish",
        "中东": "Arabic",
        "中国大陆": "中文",
        "其他": "English",
    }
    return mapping.get(target_market, "English")
