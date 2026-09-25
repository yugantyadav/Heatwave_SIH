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
    REDIS_URL: str = "redis://localhost:6379/0"
    DATA_MAX_AGE_MINUTES: int = 30
    OPEN_METEO_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """DATABASE_URL forced onto an async driver.

        Render hands out ``postgresql://user:pass@host/db`` for a Postgres
        instance. SQLAlchemy reads that as the *sync* psycopg2 dialect, so
        ``create_async_engine`` refuses it ('The asyncio extension requires
        an async driver'). Rewriting the driver is what makes the documented
        deploy config actually work.
        """
        url = self.DATABASE_URL
        for prefix in ("postgresql+psycopg2://", "postgres+psycopg2://",
                       "postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+asyncpg://" + url[len(prefix):]
        return url


settings = Settings()
