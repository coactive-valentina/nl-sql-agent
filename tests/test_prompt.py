# Unit tests for agent/prompt.py
# Tests focus on concept detection and formatting logic.
# No API calls or credentials required.

import pytest
import sys
from pathlib import Path

# Add the agent directory to the path so we can import prompt.py
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

from prompt import _format_concept_columns

MOCK_COLUMNS = [
    # base columns
    "coactive_image_id",
    "coactive_video_id",
    "coactive_shot_id",
    "keyframe_index",
    "keyframe_time_ms",
    "path",
    "created_dt",
    "metadata",
    # concept pairs
    "bobsled",
    "bobsled_prob",
    "olympics_games_now",
    "olympics_games_now_prob",
    "ck_johnny_weir",
    "ck_johnny_weir_prob",
]


def test_concept_detection():
    """Concept names are correctly detected from column list."""
    result = _format_concept_columns(MOCK_COLUMNS)

    assert "bobsled" in result
    assert "olympics_games_now" in result
    assert "ck_johnny_weir" in result


def test_base_columns_excluded():
    """Base columns do not appear as concept rows in the output."""
    result = _format_concept_columns(MOCK_COLUMNS)

    for base_col in ["coactive_image_id", "coactive_video_id", "keyframe_time_ms"]:
        # Check it doesn't appear as a concept row (starts with |)
        for line in result.split("\n"):
            if line.startswith(f"| {base_col}"):
                pytest.fail(f"Base column '{base_col}' appeared as a concept row")


def test_output_is_markdown_table():
    """Output is a valid markdown table with correct headers and rows."""
    result = _format_concept_columns(MOCK_COLUMNS)

    assert "| Column | Type | Description |" in result
    assert "|---|---|---|" in result
    assert "| bobsled_prob | float (0.0–1.0)" in result
    assert "| bobsled | integer (0 or 1)" in result


def test_no_concepts_raises_value_error():
    """ValueError is raised when only base columns are provided."""
    base_only = [
        "coactive_image_id",
        "coactive_video_id",
        "coactive_shot_id",
        "keyframe_index",
        "keyframe_time_ms",
        "path",
        "created_dt",
        "metadata",
    ]

    with pytest.raises(ValueError):
        _format_concept_columns(base_only)
