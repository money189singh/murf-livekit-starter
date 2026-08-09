import sqlite3
import json
from datetime import datetime


DATABASE_NAME = "memory.db"


def init_database():
    conn = sqlite3.connect(DATABASE_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            age_band TEXT,
            last_triage_outcome TEXT,
            last_interaction TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_user(user_id: str):
    conn = sqlite3.connect(DATABASE_NAME)

    cursor = conn.execute(
        """
        SELECT
            user_id,
            name,
            language_preference,
            age_band,
            last_triage_outcome,
            last_interaction
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "user_id": row[0],
        "name": row[1],
        "language_preference": row[2],
        "age_band": row[3],
        "last_triage_outcome": row[4],
        "last_interaction": row[5],
    }


def save_user(
    user_id: str,
    name: str | None = None,
    language_preference: str | None = None,
    age_band: str | None = None,
    last_triage_outcome: str | None = None,
):
    existing_user = get_user(user_id)

    if existing_user:
        name = name or existing_user["name"]
        language_preference = (
            language_preference or existing_user["language_preference"]
        )
        age_band = age_band or existing_user["age_band"]
        last_triage_outcome = (
            last_triage_outcome or existing_user["last_triage_outcome"]
        )

    conn = sqlite3.connect(DATABASE_NAME)

    conn.execute(
        """
        INSERT OR REPLACE INTO users (
            user_id,
            name,
            language_preference,
            age_band,
            last_triage_outcome,
            last_interaction
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            language_preference,
            age_band,
            last_triage_outcome,
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()
