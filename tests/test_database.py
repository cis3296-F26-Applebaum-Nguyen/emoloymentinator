import sqlite3

from src.core.database import (
    initialize_database,
    save_search,
    get_search_history,
    get_search_jobs,
)
from src.core.models import JobPosting, SearchRequest


def test_initialize_database(tmp_path):
    db_path = tmp_path / "history.db"

    initialize_database(db_path)

    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row[0] for row in tables}

    assert "searches" in table_names
    assert "jobs" in table_names
    assert "search_results" in table_names

def test_save_and_retrieve_search(tmp_path):
    db_path = tmp_path / "history.db"
    initialize_database(db_path)

    request = SearchRequest(search_term="Python developer")

    jobs = [
        JobPosting(title="Python Developer", company="Acme"),
        JobPosting(title="Software Engineer", company="Acme"),
    ]

    search_id = save_search(db_path, 12345, request, jobs)

    history = get_search_history(db_path, 12345)

    assert len(history) == 1
    assert history[0]["search_id"] == search_id
    assert history[0]["search_criteria"]["search_term"] == "Python developer"
    assert history[0]["retrieved_at"]

    retrieved_jobs = get_search_jobs(db_path, 12345, search_id)

    assert retrieved_jobs == jobs

def test_job_deduplication(tmp_path):
    db_path = tmp_path / "history.db"
    initialize_database(db_path)

    shared_job = JobPosting(
        title="Python Developer",
        company="Acme",
    )

    first_jobs = [
        shared_job,
        JobPosting(title="Software Engineer", company="Acme"),
    ]

    second_jobs = [
        shared_job,
        JobPosting(title="Backend Developer", company="Acme"),
    ]

    first_id = save_search(
        db_path, 12345,
        SearchRequest(search_term="Python developer"),
        first_jobs,
    )

    second_id = save_search(
        db_path, 12345,
        SearchRequest(search_term="Backend developer"),
        second_jobs,
    )

    with sqlite3.connect(db_path) as connection:
        for table, expected in [
            ("searches", 2),
            ("jobs", 3),
            ("search_results", 4),
        ]:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            assert count == expected

    assert get_search_jobs(db_path, 12345, first_id) == first_jobs
    assert get_search_jobs(db_path, 12345, second_id) == second_jobs

def test_user_search_isolation(tmp_path):
    db_path = tmp_path / "history.db"
    initialize_database(db_path)

    first_jobs = [
        JobPosting(title="Python Developer", company="Acme")
    ]

    second_jobs = [
        JobPosting(title="Data Analyst", company="Acme")
    ]

    first_id = save_search(
        db_path, 12345,
        SearchRequest(search_term="Python developer"),
        first_jobs,
    )

    second_id = save_search(
        db_path, 67890,
        SearchRequest(search_term="Data analyst"),
        second_jobs,
    )

    first_history = get_search_history(db_path, 12345)
    second_history = get_search_history(db_path, 67890)

    assert len(first_history) == 1
    assert len(second_history) == 1

    assert first_history[0]["search_id"] == first_id
    assert second_history[0]["search_id"] == second_id

    # Verify legitimate access
    assert get_search_jobs(db_path, 12345, first_id) == first_jobs
    assert get_search_jobs(db_path, 67890, second_id) == second_jobs

    # Verify unauthorized access returns nothing
    assert get_search_jobs(db_path, 12345, second_id) == []
    assert get_search_jobs(db_path, 67890, first_id) == []

def test_missing_search_history(tmp_path):
    db_path = tmp_path / "history.db"
    initialize_database(db_path)

    assert get_search_history(db_path, 12345) == []
    assert get_search_jobs(db_path, 12345, 999) == []

def test_updated_job_preserves_history(tmp_path):
    db_path = tmp_path / "history.db"
    initialize_database(db_path)

    request = SearchRequest(search_term="Python developer")

    original_job = JobPosting(
        title="Python Developer",
        company="Acme",
        url="https://example.com/job/1",
        description="Requires one year of experience.",
    )

    updated_job = JobPosting(
        title="Python Developer",
        company="Acme",
        url="https://example.com/job/1",
        description="Requires three years of experience.",
    )

    first_id = save_search(
        db_path, 12345, request, [original_job]
    )

    second_id = save_search(
        db_path, 12345, request, [updated_job]
    )

    assert get_search_jobs(db_path, 12345, first_id) == [original_job]
    assert get_search_jobs(db_path, 12345, second_id) == [updated_job]

    with sqlite3.connect(db_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0]

        assert count == 2

    history = get_search_history(db_path, 12345)

    assert [s["search_id"] for s in history] == [second_id, first_id]