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
