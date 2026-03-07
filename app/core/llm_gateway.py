import os
from langchain_openai import ChatOpenAI


class LLMGateway:

    _models = {}

    @classmethod
    def get_model(cls, model_name="gpt-4o-mini", temperature=0):

        if model_name not in cls._models:
            cls._models[model_name] = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY")
            )

        return cls._models[model_name]