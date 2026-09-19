from pydantic_settings import BaseSettings
from pydantic import Extra

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://Yugant@localhost:5432/heatwave"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"
    FORECAST_REFRESH_HOURS: int = 6
    OPEN_METEO_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""

    class Config:
        env_file = ".env"
        extra = Extra.allow

settings = Settings()