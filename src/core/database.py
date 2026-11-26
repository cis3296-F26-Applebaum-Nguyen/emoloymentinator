"""Persistent SQLite storage for user job search histories."""

import sqlite3
import json

from dataclasses import asdict
from pathlib import Path
from datetime import datetime, timezone

from .models import JobPosting, SearchRequest

SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
    search_id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    search_criteria TEXT NOT NULL,
    retrieved_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    url TEXT,
    description TEXT,
    site TEXT,
    date_posted TEXT
);

CREATE TABLE IF NOT EXISTS search_results (
    search_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    result_position INTEGER NOT NULL,
    PRIMARY KEY (search_id, result_position),
    FOREIGN KEY (search_id) REFERENCES searches(search_id)
        ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_searches_user_id
    ON searches(user_id);

CREATE INDEX IF NOT EXISTS idx_search_results_job_id
    ON search_results(job_id);
"""

def initialize_database(db_path: str | Path) -> None:
    """Create the database and its tables if they do not exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()

def _get_or_create_job(
    connection: sqlite3.Connection,
    job: JobPosting,
) -> int:
    """Return an existing identical job ID or insert a new job."""

    values = (
        job.title,
        job.company,
        job.location,
        job.url,
        job.description,
        job.site,
        job.date_posted,
    )

    existing = connection.execute(
        """
        SELECT job_id FROM jobs
        WHERE title = ?
            AND company = ?
            AND location IS ?
            AND url IS ?
            AND description IS ?
            AND site IS ?
            AND date_posted IS ?
        """,
        values,
    ).fetchone()

    if existing is not None:
        return existing[0]

    cursor = connection.execute(
        """
        INSERT INTO jobs (
            title, company, location, url,
            description, site, date_posted
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )

    return cursor.lastrowid

def save_search(
    db_path: str | Path,
    user_id: int,
    request: SearchRequest,
    jobs: list[JobPosting],
) -> int:
    """Store a user's search and its associated job listings."""

    connection = sqlite3.connect(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        cursor = connection.execute(
            """
            INSERT INTO searches (
                user_id, search_criteria, retrieved_at
            )
            VALUES (?, ?, ?)
            """,
            (
                str(user_id),
                json.dumps(asdict(request)),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        search_id = cursor.lastrowid

        for position, job in enumerate(jobs, start=1):
            job_id = _get_or_create_job(connection, job)

            connection.execute(
                """
                INSERT INTO search_results (
                    search_id, job_id, result_position
                )
                VALUES (?, ?, ?)
                """,
                (search_id, job_id, position),
            )

        connection.commit()
        return search_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def get_search_history(
    db_path: str | Path,
    user_id: int,
) -> list[dict]:
    """Retrieve a user's previous searches, newest first."""

    connection = sqlite3.connect(db_path)

    try:
        rows = connection.execute(
            """
            SELECT search_id, search_criteria, retrieved_at
            FROM searches
            WHERE user_id = ?
            ORDER BY retrieved_at DESC, search_id DESC
            """,
            (str(user_id),),
        ).fetchall()

        return [
            {
                "search_id": row[0],
                "search_criteria": json.loads(row[1]),
                "retrieved_at": row[2],
            }
            for row in rows
        ]

    finally:
        connection.close()

def get_search_jobs(
    db_path: str | Path,
    user_id: int,
    search_id: int,
) -> list[JobPosting]:
    """Retrieve jobs from a search belonging to the specified user."""

    connection = sqlite3.connect(db_path)

    try:
        rows = connection.execute(
            """
            SELECT jobs.title, jobs.company, jobs.location,
                   jobs.url, jobs.description, jobs.site,
                   jobs.date_posted
            FROM jobs
            JOIN search_results
                ON jobs.job_id = search_results.job_id
            JOIN searches
                ON searches.search_id = search_results.search_id
            WHERE searches.user_id = ?
                AND searches.search_id = ?
            ORDER BY search_results.result_position
            """,
            (str(user_id), search_id),
        ).fetchall()

        return [JobPosting(*row) for row in rows]

    finally:
        connection.close()