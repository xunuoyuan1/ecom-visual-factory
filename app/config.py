from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    vision_model: str = Field(default="gpt-5.5", alias="VISION_MODEL")
    reasoning_model: str = Field(default="gpt-5.5", alias="REASONING_MODEL")
    qa_model: str = Field(default="gpt-5.5", alias="QA_MODEL")
    enable_web_enhancement: bool = Field(default=True, alias="ENABLE_WEB_ENHANCEMENT")
    max_qa_iterations: int = Field(default=1, alias="MAX_QA_ITERATIONS")


settings = Settings()
