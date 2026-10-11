# src/tools/__init__.py
from tools.note import (
    save_note,
    search_notes,
    TOOLS as NOTE_TOOLS,
)

# What is called when model requests to add
def add(a: int, b: int) -> int:
    return a + b

# Tool Schema: tell the model what it may request
ADD_TOOL = {
    "type": "function",
    "function": {
        "name": "add",
        "description": "Add two whole numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
    },
}

# Configuration for the tools
TOOLS = [ADD_TOOL, *NOTE_TOOLS]
ALLOWED_TOOLS = {
    "add": add,
    "save_note": save_note,
    "search_notes": search_notes,
}
# Maximum model responses for one user message, including tool requests.
# Multiple tool calls in one response count as one turn.
# Tool errors still consume the turn that requested them.
# If the final response requests tools, those tools are not executed.
MAX_MODEL_TURNS = 10
