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
