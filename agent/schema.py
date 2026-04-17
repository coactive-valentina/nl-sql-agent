# Discovers the schema of coactive_table_adv by running a LIMIT 1 query
# and returning the full list of column names for a given dataset.

import os
from dotenv import load_dotenv
from .coactive import get_columns

load_dotenv()

DISCOVERY_QUERY = "SELECT * FROM coactive_table_adv LIMIT 1"


def get_schema(dataset_id: str) -> list[str]:
    """
    Returns the full list of column names from coactive_table_adv
    for the given dataset.

    Args:
        dataset_id: The Coactive dataset ID to query.

    Returns:
        A list of column name strings.
    """
    return get_columns(DISCOVERY_QUERY, dataset_id)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    dataset_id = os.getenv("COACTIVE_DATASET_ID")
    print(f"Using dataset ID: {dataset_id}")

    columns = get_schema(dataset_id)
    print(f"Total columns: {len(columns)}")
    print("Column names:")
    for col in columns:
        print(f"  - {col}")