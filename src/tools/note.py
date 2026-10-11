import sqlite3


DB_PATH = "notes.db"


def init_db():
    """
    Create a new table only if it doesn't exist.
    """
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        """)


init_db()


def save_note(note: str) -> str:
    """
    Persist convo to a long-term memory
    """
    note = note.strip()
    with sqlite3.connect(DB_PATH) as connection:
        existing = connection.execute(
            "SELECT 1 FROM notes "
            "WHERE content = ? COLLATE NOCASE LIMIT 1",
            (note,),
        ).fetchone()

        if existing:
            return f"Already saved: {note}"

        connection.execute(
            "INSERT INTO notes (content) VALUES (?)",
            (note,),
        )
    return f"Saved the note: {note}"


def search_notes(query: str = "*") -> str:
    """
    Search long-term memory, or return all for "*".
    """
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, content FROM notes"
        ).fetchall()
    notes = [f"{row['id']}: {row['content']}" for row in rows]

    # return all notes
    if query == "*":
        return "\n".join(notes)

    matches = [
        note for note in notes
        if query.casefold() in note.casefold()
    ]
    if not matches:
        return "No matching notes found"

    return "\n".join(matches)


TOOLS = [{
    "type": "function",
    "function": {
        "name": "save_note",
        "description": "Save a note",
        "parameters": {
            "type": "object",
            "properties": {
                "note": {"type": "string"}
            },
            "required": ["note"],
            "additionalProperties": False
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "search_notes",
        "description": "Search notes. Searching '*' means 'all notes'.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"],
            "additionalProperties": False
        }
    }
}]
