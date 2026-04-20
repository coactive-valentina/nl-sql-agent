# Unit tests for agent/agent.py
# All external dependencies (OpenAI, Coactive, file system) are mocked.
# No API calls or credentials required.

import json
import pytest
from unittest.mock import patch

from agent.agent import run

MOCK_QUESTION = "how many videos are in the dataset?"
MOCK_DATASET_ID = "bb909094-21ba-49b4-863f-ac5edb9af0b6"
MOCK_COLUMNS = ["coactive_video_id", "bobsled", "bobsled_prob"]
MOCK_PROMPT = "you are a sql agent..."
MOCK_SQL = "SELECT COUNT(DISTINCT coactive_video_id) AS total_videos FROM coactive_table_adv;"
MOCK_RESULTS = [{"total_videos": 598}]


@pytest.fixture
def mock_dependencies():
    """Patches all external dependencies with happy path defaults."""
    with patch("agent.agent.get_schema") as mock_schema, \
         patch("agent.agent.build_prompt") as mock_prompt, \
         patch("agent.agent._call_openai") as mock_openai, \
         patch("agent.agent.execute_query") as mock_execute:

        mock_schema.return_value = MOCK_COLUMNS
        mock_prompt.return_value = MOCK_PROMPT
        mock_openai.return_value = MOCK_SQL
        mock_execute.return_value = MOCK_RESULTS

        yield {
            "schema": mock_schema,
            "prompt": mock_prompt,
            "openai": mock_openai,
            "execute": mock_execute,
        }


@pytest.fixture
def log_file(tmp_path):
    """Creates a temporary interactions.json file for testing."""
    log = tmp_path / "interactions.json"
    log.write_text("[]")
    return log


def test_run_returns_correct_structure(mock_dependencies, log_file):
    """run() returns a dict with the correct keys and values."""
    with patch("agent.agent.LOGS_PATH", log_file):
        result = run(MOCK_QUESTION, MOCK_DATASET_ID)

    assert result["question"] == MOCK_QUESTION
    assert result["sql"] == MOCK_SQL
    assert result["results"] == MOCK_RESULTS
    assert result["error"] is None


def test_run_logs_interaction(mock_dependencies, log_file):
    """run() appends a correctly structured entry to interactions.json."""
    with patch("agent.agent.LOGS_PATH", log_file):
        run(MOCK_QUESTION, MOCK_DATASET_ID)

    entries = json.loads(log_file.read_text())

    assert len(entries) == 1
    entry = entries[0]
    assert entry["question"] == MOCK_QUESTION
    assert entry["sql"] == MOCK_SQL
    assert entry["error"] is None
    assert "timestamp" in entry
    assert "result_count" in entry


def test_run_handles_error_gracefully(mock_dependencies, log_file):
    """run() returns error dict when execute_query raises an exception."""
    mock_dependencies["execute"].side_effect = Exception("Coactive API error")

    with patch("agent.agent.LOGS_PATH", log_file):
        result = run(MOCK_QUESTION, MOCK_DATASET_ID)

    assert result["error"] == "Coactive API error"
    assert result["results"] == []
    assert result["question"] == MOCK_QUESTION


def test_run_error_is_logged(mock_dependencies, log_file):
    """run() logs the interaction even when an error occurs."""
    mock_dependencies["execute"].side_effect = Exception("Coactive API error")

    with patch("agent.agent.LOGS_PATH", log_file):
        run(MOCK_QUESTION, MOCK_DATASET_ID)

    entries = json.loads(log_file.read_text())

    assert len(entries) == 1
    assert entries[0]["error"] == "Coactive API error"
    assert entries[0]["question"] == MOCK_QUESTION
