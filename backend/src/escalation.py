import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).parent / "health_access.db"


def init_escalation_database():
    """Create the escalation table if it does not already exist."""

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE NOT NULL,
            user_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            summary TEXT NOT NULL,
            urgency TEXT NOT NULL,
            language TEXT,
            preferred_followup TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def create_escalation(
    user_id: str,
    reason: str,
    summary: str,
    urgency: str,
    language: str,
    preferred_followup: str,
):
    """
    Create a human-help request.

    Only call this function after the caller has explicitly
    given permission to share the limited information.
    """

    reference_id = (
        f"ESC-{datetime.now().strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    created_at = datetime.now().isoformat(timespec="seconds")

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO escalations (
            reference_id,
            user_id,
            reason,
            summary,
            urgency,
            language,
            preferred_followup,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            reference_id,
            user_id,
            reason,
            summary,
            urgency,
            language,
            preferred_followup,
            "open",
            created_at,
        ),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "reference_id": reference_id,
        "status": "open",
        "message": "Human assistance request created successfully.",
    }
