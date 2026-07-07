from harness.parser import parse_actions
from harness.models import Action

def test_parse_single_action():
    text = '<action name="bash" args=\'{"command": "ls"}\' />'
    actions = parse_actions(text)
    assert len(actions) == 1
    assert actions[0].name == "bash"
    assert actions[0].args["command"] == "ls"

def test_parse_multiple_actions():
    text = '<action name="read" args=\'{"file_path": "a.py"}\' />\n<action name="bash" args=\'{"command": "pytest"}\' />'
    actions = parse_actions(text)
    assert len(actions) == 2
    assert actions[0].name == "read"
    assert actions[1].name == "bash"

def test_parse_no_actions_returns_empty():
    actions = parse_actions("just plain text, no actions")
    assert actions == []

def test_parse_malformed_returns_empty():
    actions = parse_actions('<action name="bash" args={bad json} />')
    assert actions == []
