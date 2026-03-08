from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.config import settings


class LLMGateway:

    _model = None

    @classmethod
    def get_model(cls):

        if cls._model:
            return cls._model

        if settings.LLM_PROVIDER == "openai":

            cls._model = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0)

        elif settings.LLM_PROVIDER == "ollama":

            cls._model = ChatOllama(
                model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_URL, temperature=0
            )

        else:
            raise ValueError("Unsupported LLM provider")

        return cls._model
