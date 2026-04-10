# Discovers the schema of coactive_table_adv by running a LIMIT 1 query
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://app.coactive.ai/api/v1/queries"
TIMEOUT = 300  # seconds


def get_schema(dataset_id: str) -> list[str]:
    """
    Submits a LIMIT 1 discovery query to the Coactive API and returns
    the full list of column names from coactive_table_adv.

    Args:
        dataset_id: The Coactive dataset ID to query.

    Returns:
        A list of column name strings.

    Raises:
        EnvironmentError: If credentials are missing.
        Exception: If the query submission or execution fails.
        TimeoutError: If the query does not complete within TIMEOUT seconds.
    """
    client_id = os.getenv("COACTIVE_CLIENT_ID")
    client_secret = os.getenv("COACTIVE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "COACTIVE_CLIENT_ID and COACTIVE_CLIENT_SECRET must be set in your .env file."
        )

    headers = {
        "Authorization": f"Bearer {client_id}:{client_secret}",
        "Content-Type": "application/json",
    }

    # Step 1 — Submit discovery query
    payload = {
        "query": "SELECT * FROM coactive_table_adv LIMIT 1",
        "datasetId": dataset_id,
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(
            f"Failed to submit schema discovery query: {response.text}"
        )

    query_id = response.json().get("queryId")

    if not query_id:
        raise Exception(
            "Schema discovery query submitted but no queryId was returned."
        )

    # Step 2 — Poll until complete
    poll_url = f"{API_URL}/{query_id}"
    start_time = time.time()

    while True:
        if time.time() - start_time > TIMEOUT:
            raise TimeoutError(
                f"Schema discovery query timed out after {TIMEOUT} seconds."
            )

        poll_response = requests.get(poll_url, headers=headers)

        if poll_response.status_code != 200:
            raise Exception(
                f"Failed to poll schema discovery query: {poll_response.text}"
            )

        result = poll_response.json()
        status = result.get("status")

        if status == "Complete":
            break
        elif status == "Failed":
            raise Exception(
                f"Schema discovery query failed: {result}"
            )

        time.sleep(2)

    # Step 3 — Extract column names
    data = result.get("result", {}).get("data", [])

    if not data:
        raise Exception(
            "Schema discovery query returned no data. "
            "Check that the dataset ID is correct and the table is not empty."
        )

    columns = list(data[0]["data"].keys())
    return columns

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    dataset_id = os.getenv("COACTIVE_DATASET_ID")
    print(f"Using dataset ID: {dataset_id}")

    columns = get_schema(dataset_id)
    print(f"Total columns: {len(columns)}")
    print("Column names:")
    for col in columns:
        print(f"  - {col}")
# and returning the full list of column names for a given dataset.