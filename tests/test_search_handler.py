from src.bot.commands import placeholder_results


def test_placeholder_search_returns_jobs():
    jobs = placeholder_results("Python developer")
    assert len(jobs) == 5
    assert "Python developer" in jobs[0].title
