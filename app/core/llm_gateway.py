import os

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


class LLMGateway:

    _model = None

    @classmethod
    def get_model(cls):

        if cls._model:
            return cls._model

        provider = os.getenv("LLM_PROVIDER", "openai")

        if provider == "openai":

            cls._model = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0
            )

        elif provider == "ollama":

            cls._model = ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "llama3.2"),
                base_url="http://localhost:11434",
                temperature=0
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        return cls._model