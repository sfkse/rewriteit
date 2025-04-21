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
    client_base_url: str
    slack_bot_token: str
    api_port: str 
    db_port: str 
    ssl_cert_path: str
    ssl_key_path: str 
    use_ssl: bool
    logtail_source_token: str
    logtail_host: str
    env: str

    class Config:       
        env_file = ".env"

settings = Settings() 