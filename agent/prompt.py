# Builds the final prompt string to send to OpenAI by injecting the
# discovered schema and user question into the Jinja2 template.

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

TEMPLATE_FILE = "sql_agent.j2"
TEMPLATE_DIR = Path(__file__).parent / "prompts"

BASE_COLUMNS = {
    "coactive_image_id",
    "coactive_video_id",
    "coactive_shot_id",
    "keyframe_index",
    "keyframe_time_ms",
    "path",
    "created_dt",
    "metadata",
}


def _format_concept_columns(columns: list[str]) -> str:
    """
    Takes the raw list of column names from schema.py, filters out base
    columns, detects concept pairs, and returns a markdown table string
    ready to inject into the prompt template.

    Args:
        columns: Raw list of column names from get_schema().

    Returns:
        A markdown table string listing all concept columns.

    Raises:
        ValueError: If no concept columns are detected after filtering.
    """
    # Find all concept names by looking for _prob columns
    concept_names = [
        col.removesuffix("_prob")
        for col in columns
        if col.endswith("_prob") and col not in BASE_COLUMNS
    ]

    if not concept_names:
        raise ValueError(
            "No concept columns detected in the schema. "
            "Check that the dataset has been processed and concepts have been created."
        )

    # Build markdown table
    rows = ["| Column | Type | Description |", "|---|---|---|"]
    for concept in concept_names:
        rows.append(
            f"| {concept} | integer (0 or 1) | binary flag for {concept} concept |"
        )
        rows.append(
            f"| {concept}_prob | float (0.0–1.0) | probability score for {concept} concept |"
        )

    return "\n".join(rows)


def build_prompt(
    user_question: str,
    dataset_id: str,
    columns: list[str],
) -> str:
    """
    Renders the sql_agent.j2 template with the user question, dataset ID,
    and dynamically discovered concept columns.

    Args:
        user_question: The natural language question from the user.
        dataset_id: The Coactive dataset ID to query.
        columns: Raw list of column names from get_schema().

    Returns:
        The fully rendered prompt string ready to send to OpenAI.

    Raises:
        FileNotFoundError: If the template file cannot be found.
        ValueError: If no concept columns are detected.
    """
    try:
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        template = env.get_template(TEMPLATE_FILE)
    except TemplateNotFound:
        raise FileNotFoundError(
            f"Template file '{TEMPLATE_FILE}' not found in {TEMPLATE_DIR}. "
            "Make sure agent/prompts/sql_agent.j2 exists."
        )

    concept_columns = _format_concept_columns(columns)

    return template.render(
        user_question=user_question,
        dataset_id=dataset_id,
        concept_columns=concept_columns,
    )


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from schema import get_schema

    load_dotenv()

    dataset_id = os.getenv("COACTIVE_DATASET_ID")
    test_question = "How many distinct videos are in the dataset?"

    print("Fetching schema...")
    columns = get_schema(dataset_id)
    print(f"Schema fetched — {len(columns)} columns found\n")

    print("Building prompt...")
    prompt = build_prompt(test_question, dataset_id, columns)
    print("=" * 60)
    print(prompt)
    print("=" * 60)
