from dotenv import load_dotenv
import os

env = os.getenv("ENV", "dev") # 기본값은 dev

if env == "prod":
    load_dotenv(dotenv_path=".env.prod")
else:
    load_dotenv(dotenv_path=".env.dev")

class Settings:
    ENV = os.getenv("ENV")
    DB_URL = os.getenv("DB_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

settings = Settings()