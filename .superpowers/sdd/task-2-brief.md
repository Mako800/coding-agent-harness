# Task 2: LLM Abstraction Layer

**Files:**
- Create: `src/harness/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: `Message` from Task 1
- Produces: `LLM` (abstract base), `MockLLM(responses: list[str])`, `DeepSeekLLM(api_key: str, model: str)`

## Step 1: Write the failing test

```python
# tests/test_llm.py
from harness.models import Message
from harness.llm import LLM, MockLLM

def test_mock_llm_returns_responses_in_order():
    llm = MockLLM(responses=["first", "second", "third"])
    msgs = [Message(role="user", content="hi")]
    assert llm.ask(msgs) == "first"
    assert llm.ask(msgs) == "second"
    assert llm.ask(msgs) == "third"

def test_mock_llm_raises_when_exhausted():
    import pytest
    llm = MockLLM(responses=["only"])
    llm.ask([Message(role="user", content="x")])
    with pytest.raises(IndexError):
        llm.ask([Message(role="user", content="x")])

def test_llm_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        LLM()
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_llm.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

```python
# src/harness/llm.py
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
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_llm.py -v`
Expected: PASS (3 tests)

## Step 5: Commit

```bash
git add src/harness/llm.py tests/test_llm.py
git commit -m "feat(llm): add LLM abstraction with MockLLM and DeepSeekLLM"
```
