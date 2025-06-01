import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class EnvConfig:
    model_is_azure: bool
    model_name: str
    base_url: Optional[str]
    api_key: str

    @classmethod
    def from_env(cls) -> "EnvConfig":
        model_is_azure = os.getenv("MODEL_IS_AZURE", "false").lower() == "true"
        model_name = os.getenv("MODEL_NAME", "google/gemini-2.5-flash-preview")
        base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
        api_key = os.getenv("API_KEY", "")
        if not api_key:
            raise ValueError("API_KEY Not Found")
        return cls(
            model_is_azure=model_is_azure,
            model_name=model_name,
            base_url=base_url,
            api_key=api_key
        )


env_config = EnvConfig.from_env()
