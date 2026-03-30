from pathlib import Path

from src.data.leaderboard import LocalLeaderboard


def test_failed_attempt_increments_attempts_only(tmp_path: Path) -> None:
    leaderboard = LocalLeaderboard(tmp_path / "leaderboard.json")
    leaderboard.record_attempt(0)

    assert leaderboard.data.attempts == 1
    assert leaderboard.data.successes == 0
    assert leaderboard.data.recent_results[0].result == 0


def test_success_attempt_increments_attempts_and_successes(tmp_path: Path) -> None:
    leaderboard = LocalLeaderboard(tmp_path / "leaderboard.json")
    leaderboard.record_attempt(1)

    assert leaderboard.data.attempts == 1
    assert leaderboard.data.successes == 1
    assert leaderboard.data.recent_results[0].result == 1
