import os

from dotenv import load_dotenv

load_dotenv()


class Settings:

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

    OTEL_ENDPOINT = os.getenv("OTEL_ENDPOINT", "http://localhost:4317")


settings = Settings()
