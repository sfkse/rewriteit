from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    slack_client_id: str
    slack_client_secret: str
    slack_api_base_url: str
    slack_signing_secret: str
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str
    database_url: str
    api_base_url: str
    slack_bot_token: str
    
    class Config:       
        env_file = ".env"

settings = Settings() 