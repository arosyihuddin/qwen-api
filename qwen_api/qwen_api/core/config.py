from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_base: str = "https://chat.qwen.ai/api"
    model_default: str = "qwen-max-latest"
    
    class Config:
        env_file = ".env"