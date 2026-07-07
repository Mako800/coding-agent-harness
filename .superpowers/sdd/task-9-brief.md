# Task 9: Action Parser

**Files:**
- Create: `src/harness/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Produces: `parse_actions(text: str) -> list[Action]` — parses `<action name="X" args='{"k":"v"}' />` tags

## Step 1: Write the failing test

```python
# tests/test_parser.py
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
```

## Step 2: Run test to verify it fails

Run: `pytest tests/test_parser.py -v`
Expected: FAIL with `ModuleNotFoundError`

## Step 3: Write minimal implementation

```python
# src/harness/parser.py
import re
import json
from .models import Action

_ACTION_RE = re.compile(r'<action\s+name="([^"]+)"\s+args=\'([^\']*)\'\s*/>')

def parse_actions(text: str) -> list[Action]:
    actions = []
    for m in _ACTION_RE.finditer(text):
        name = m.group(1)
        try:
            args = json.loads(m.group(2))
        except json.JSONDecodeError:
            continue
        actions.append(Action(name=name, args=args))
    return actions
```

## Step 4: Run test to verify it passes

Run: `pytest tests/test_parser.py -v`
Expected: PASS (4 tests)

## Step 5: Commit

```bash
git add src/harness/parser.py tests/test_parser.py
git commit -m "feat(parser): add LLM output action parser"
```
