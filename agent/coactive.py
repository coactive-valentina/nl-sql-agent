# Handles all communication with the Coactive API.
# Submits SQL queries, polls for results, and returns data as a list of dicts.

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://app.coactive.ai/api/v1/queries"
TIMEOUT = 300   # seconds before giving up on a query
POLL_INTERVAL = 5  # seconds between polling attempts
PAGE_SIZE = 10000  # rows per page for pagination


def _build_headers() -> dict:
    """
    Builds the auth headers from environment variables.

    Raises:
        EnvironmentError: If credentials are missing.
    """
    client_id = os.getenv("COACTIVE_CLIENT_ID")
    client_secret = os.getenv("COACTIVE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "COACTIVE_CLIENT_ID and COACTIVE_CLIENT_SECRET must be set in your .env file."
        )

    return {
        "Authorization": f"Bearer {client_id}:{client_secret}",
        "Content-Type": "application/json",
    }


def _submit_and_poll(sql: str, dataset_id: str, headers: dict) -> dict:
    """
    Submits a SQL query to the Coactive API and polls until complete.

    Args:
        sql: The SQL query string to execute.
        dataset_id: The Coactive dataset ID to query against.
        headers: Auth headers built by _build_headers().

    Returns:
        The full API response dict when status is Complete.

    Raises:
        Exception: If submission fails or query status is Failed.
        TimeoutError: If query does not complete within TIMEOUT seconds.
    """
    # Submit query
    payload = {"query": sql, "datasetId": dataset_id}
    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(
            f"Failed to submit query to Coactive: {response.text}"
        )

    query_id = response.json().get("queryId")

    if not query_id:
        raise Exception("Query submitted but no queryId was returned.")

    # Poll until complete
    poll_url = f"{API_URL}/{query_id}"
    start_time = time.time()

    while True:
        if time.time() - start_time > TIMEOUT:
            raise TimeoutError(
                f"Query {query_id} timed out after {TIMEOUT} seconds."
            )

        poll_response = requests.get(poll_url, headers=headers)

        if poll_response.status_code != 200:
            raise Exception(
                f"Failed to poll query {query_id}: {poll_response.text}"
            )

        result = poll_response.json()
        status = result.get("status")

        if status == "Complete":
            return result
        elif status == "Failed":
            raise Exception(f"Query {query_id} failed: {result}")

        time.sleep(POLL_INTERVAL)


def execute_query(sql: str, dataset_id: str) -> list[dict]:
    """
    Executes a SQL query against Coactive with pagination and returns
    all results as a list of dicts.

    Args:
        sql: The SQL query string to execute.
        dataset_id: The Coactive dataset ID to query against.

    Returns:
        A list of dicts, one per row. Empty list if no results.

    Raises:
        EnvironmentError: If credentials are missing.
        Exception: If the query fails.
        TimeoutError: If the query times out.
    """
    headers = _build_headers()
    all_rows = []
    offset = 0

    while True:
        paginated_sql = f"{sql.rstrip(';')} LIMIT {PAGE_SIZE} OFFSET {offset};"
        result = _submit_and_poll(paginated_sql, dataset_id, headers)

        rows = [
            item["data"]
            for item in result.get("result", {}).get("data", [])
        ]

        all_rows.extend(rows)
        offset += PAGE_SIZE

        if len(rows) < PAGE_SIZE:
            break  # last page reached

    return all_rows


def get_columns(sql: str, dataset_id: str) -> list[str]:
    """
    Executes a SQL query and returns only the column names from the
    first row. Used by schema.py for schema discovery.

    Args:
        sql: The SQL query string (should use LIMIT 1).
        dataset_id: The Coactive dataset ID to query against.

    Returns:
        A list of column name strings.

    Raises:
        Exception: If the query returns no data.
    """
    headers = _build_headers()
    result = _submit_and_poll(sql, dataset_id, headers)

    data = result.get("result", {}).get("data", [])

    if not data:
        raise Exception(
            "Schema discovery query returned no data. "
            "Check that the dataset ID is correct and the table is not empty."
        )

    return list(data[0]["data"].keys())


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    dataset_id = os.getenv("COACTIVE_DATASET_ID")

    print("Testing execute_query with a simple aggregation...")
    rows = execute_query(
        "SELECT COUNT(DISTINCT coactive_video_id) AS total_videos FROM coactive_table_adv",
        dataset_id,
    )
    print(f"Result: {rows}")
