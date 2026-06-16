from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    vision_model: str = Field(default="gpt-5.5", alias="VISION_MODEL")
    reasoning_model: str = Field(default="gpt-5.5", alias="REASONING_MODEL")
    qa_model: str = Field(default="gpt-5.5", alias="QA_MODEL")
    image_model: str = Field(default="gpt-image-2", alias="IMAGE_MODEL")
    enable_web_enhancement: bool = Field(default=True, alias="ENABLE_WEB_ENHANCEMENT")
    enable_image_generation: bool = Field(default=False, alias="ENABLE_IMAGE_GENERATION")
    max_qa_iterations: int = Field(default=1, alias="MAX_QA_ITERATIONS")


settings = Settings()
