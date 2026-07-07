from abc import ABC, abstractmethod
from .models import Message

class LLM(ABC):
    @abstractmethod
    def ask(self, messages: list[Message]) -> str:
        ...

class MockLLM(LLM):
    def __init__(self, responses: list[str]):
        self._responses = responses
        self._index = 0

    def ask(self, messages: list[Message]) -> str:
        response = self._responses[self._index]
        self._index += 1
        return response

class DeepSeekLLM(LLM):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self._api_key = api_key
        self._model = model

    def ask(self, messages: list[Message]) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return resp.choices[0].message.content
