from pydantic_settings import BaseSettings

# TODO: Перенести всё в Pydantic

# Настройки сети
IFACE = "Realtek Gaming 2.5GbE Family Controller"
TARGET_NETWORK = "192.168.1.0/24"
PAUSE_TIME = 1.0


class Settings(BaseSettings):
    # Настройки Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Режим управления
    USE_WEB_CONTROL: bool = False  # Если False, демон игнорирует Redis
    STREAM_NAME: str = "signal:commands"

    class Config:
        env_file = ".env"


settings = Settings()