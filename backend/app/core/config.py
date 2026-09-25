from pydantic_settings import BaseSettings, SettingsConfigDict
import os

_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(_BACKEND_DIR, ".env"),
        extra="allow",
    )

    DATABASE_URL: str = f"sqlite+aiosqlite:///{os.path.join(_BACKEND_DIR, 'heatwave.db')}"
    ENVIRONMENT: str = "development"
    FORECAST_REFRESH_HOURS: int = 6
    ALERT_COOLDOWN_HOURS: int = 6
    MANUAL_ALERT_WINDOW_SECONDS: int = 300
    OPEN_METEO_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""

settings = Settings()
