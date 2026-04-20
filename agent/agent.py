# Orchestrates the full NL → SQL → Coactive → results pipeline.
# The run() function is the public interface used by both the terminal
# loop and the FastAPI backend on Day 2.

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .coactive import execute_query
from .prompt import build_prompt
from .schema import get_schema

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL")
LOGS_PATH = Path(__file__).parent.parent / "logs" / "interactions.json"


def _call_openai(prompt: str) -> str:
    """
    Sends the rendered prompt to OpenAI and returns the generated SQL string.

    Args:
        prompt: The fully rendered prompt string from build_prompt().

    Returns:
        The SQL query string returned by the model.

    Raises:
        Exception: If the OpenAI API call fails.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content.strip()


def _log_interaction(entry: dict) -> None:
    """
    Appends an interaction entry to logs/interactions.json.

    Args:
        entry: Dict containing question, sql, result_count, error, timestamp.
    """
    try:
        existing = json.loads(LOGS_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    existing.append(entry)
    LOGS_PATH.write_text(json.dumps(existing, indent=2))


def run(question: str, dataset_id: str) -> dict:
    """
    Runs the full NL → SQL → Coactive → results pipeline.

    Args:
        question: The natural language question from the user.
        dataset_id: The Coactive dataset ID to query against.

    Returns:
        A dict with keys: question, sql, results, error.
    """
    sql = None
    results = []
    error = None

    try:
        # Step 1 — Discover schema
        columns = get_schema(dataset_id)

        # Step 2 — Build prompt
        prompt = build_prompt(question, dataset_id, columns)

        # Step 3 — Generate SQL
        sql = _call_openai(prompt)

        # Step 4 — Execute query
        results = execute_query(sql, dataset_id)

    except Exception as e:
        error = str(e)

    # Step 5 — Log interaction
    _log_interaction({
        "timestamp": datetime.now(UTC).isoformat(),
        "question": question,
        "sql": sql,
        "result_count": len(results),
        "error": error,
    })

    return {
        "question": question,
        "sql": sql,
        "results": results,
        "error": error,
    }


def main():
    """Terminal loop for Day 1 demo."""
    dataset_id = os.getenv("COACTIVE_DATASET_ID")

    if not dataset_id:
        print("Error: COACTIVE_DATASET_ID not set in .env file.")
        return

    print("\n=== NL-SQL Agent ===")
    print(f"Dataset: {dataset_id}")
    print("Type your question or 'quit' to exit.\n")

    while True:
        question = input("Question: ").strip()

        if not question:
            continue

        if question.lower() == "quit":
            print("Goodbye!")
            break

        print("\nThinking...")
        result = run(question, dataset_id)

        if result["error"]:
            print(f"\nError: {result['error']}")
        else:
            print(f"\nSQL:\n{result['sql']}")
            print(f"\nResults:\n{json.dumps(result['results'], indent=2)}")

        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    main()
