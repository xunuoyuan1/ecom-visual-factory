import os

from pydantic import Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    BaseSettings = None
    SettingsConfigDict = None


if BaseSettings is not None:

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

        openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
        openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
        llm_mode: str = Field(default="mock", alias="LLM_MODE")
        vision_model: str = Field(default="gpt-5.5", alias="VISION_MODEL")
        reasoning_model: str = Field(default="gpt-5.5", alias="REASONING_MODEL")
        qa_model: str = Field(default="gpt-5.5", alias="QA_MODEL")
        image_model: str = Field(default="gpt-image-2", alias="IMAGE_MODEL")
        enable_web_enhancement: bool = Field(default=True, alias="ENABLE_WEB_ENHANCEMENT")
        enable_image_generation: bool = Field(default=False, alias="ENABLE_IMAGE_GENERATION")
        max_qa_iterations: int = Field(default=1, alias="MAX_QA_ITERATIONS")

else:

    def _env_bool(name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.lower() in {"1", "true", "yes", "on"}


    class Settings:
        openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        llm_mode: str = os.getenv("LLM_MODE", "mock")
        vision_model: str = os.getenv("VISION_MODEL", "gpt-5.5")
        reasoning_model: str = os.getenv("REASONING_MODEL", "gpt-5.5")
        qa_model: str = os.getenv("QA_MODEL", "gpt-5.5")
        image_model: str = os.getenv("IMAGE_MODEL", "gpt-image-2")
        enable_web_enhancement: bool = _env_bool("ENABLE_WEB_ENHANCEMENT", True)
        enable_image_generation: bool = _env_bool("ENABLE_IMAGE_GENERATION", False)
        max_qa_iterations: int = int(os.getenv("MAX_QA_ITERATIONS", "1"))


settings = Settings()
