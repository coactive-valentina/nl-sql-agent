# Coactive Platform — Agent Context Reference

This document is the source of truth for how the agent understands and queries the Coactive platform. It is used to build the prompt sent to OpenAI and should be updated whenever the data model or query patterns change.

---

## What is Coactive?

Coactive is a visual analytics platform that processes video and image datasets using AI. It generates metadata from visual content by detecting **concepts** — custom visual patterns defined by the user — and stores the results in queryable SQL tables.

---

## Data Hierarchy

Each row in `coactive_table_adv` represents a single **keyframe** (image) extracted from a video. The hierarchy is:

```
video (coactive_video_id)
  └── shot (coactive_shot_id)
        └── keyframe / image (coactive_image_id)
```

- A **video** contains multiple shots
- A **shot** is a continuous camera take, containing multiple keyframes
- A **keyframe** is a single image extracted from the video at a specific timestamp

---

## Primary Table: `coactive_table_adv`

This is the main table used for all queries. It is a **keyframe-level** table — one row per keyframe.

### Fixed Base Columns (always present)

| Column | Description | Type |
|---|---|---|
| `coactive_image_id` | Unique identifier for the keyframe/image | string |
| `coactive_video_id` | Unique identifier for the video | string |
| `coactive_shot_id` | Unique identifier for the shot | string |
| `keyframe_index` | Index of the keyframe within the asset | string |
| `keyframe_time_ms` | Start time of the keyframe in milliseconds | float |
| `path` | Storage path of the keyframe | string |
| `created_dt` | Timestamp of video ingestion | timestamp |
| `metadata` | File-level metadata | JSON |

### Dynamic Concept Columns (vary per dataset)

For every concept defined in the dataset, two columns are added:

| Column Pattern | Description | Type |
|---|---|---|
| `[concept_name]` | Binary flag: 1 if concept detected, 0 if not. Default threshold: 0.7 on `_prob` | integer (0 or 1) |
| `[concept_name]_prob` | Probability score: likelihood the concept applies to this keyframe | float (0.0 – 1.0) |

**Example:** if a concept named `slam_dunk` exists, the table will have:
- `slam_dunk` → binary (0 or 1)
- `slam_dunk_prob` → float between 0.0 and 1.0

---

## What are Concepts?

Concepts are custom visual patterns defined by users in the Coactive platform. They are trained using positive and negative examples from the dataset. Once processed, every keyframe in the dataset receives a probability score for each concept.

**Examples of concepts:**
- `slam_dunk` — detects slam dunk moments in basketball footage
- `aerial_shots` — detects drone or aerial camera angles
- `bobsled` — detects bobsled activity in sports footage
- `ck_snoop_dogg2` — detects a specific person (Snoop Dogg) in footage

Concepts are **dataset-specific** — different datasets will have different concept columns.

---

## Schema Discovery

Because concept columns are dynamic, the agent must discover the schema at runtime before generating SQL.

### Step 1 — Discover available tables
```sql
SHOW TABLES
```
Returns all tables available for the active dataset, including dynamic tag tables.

### Step 2 — Discover concept columns
```sql
SELECT * FROM coactive_table_adv LIMIT 1
```
Returns one row with all column names. The agent parses the response to identify concept columns.

**How to detect concept columns:**
- Remove the fixed base columns listed above
- Any remaining column is a concept column
- Columns ending in `_prob` are probability scores
- The matching root name (without `_prob`) is the binary flag column
- Concepts come in pairs: `[concept_name]` and `[concept_name]_prob`

---

## Coactive API — Query Execution

Queries are not executed directly against a local database. They are submitted to the Coactive API as SQL and results are retrieved via polling.

### Authentication
All requests use Bearer token authentication:
```
Authorization: Bearer {CLIENT_ID}:{CLIENT_SECRET}
Content-Type: application/json
```

### Step 1 — Submit a query
```
POST https://app.coactive.ai/api/v1/queries
Body: { "query": "<SQL>", "datasetId": "<DATASET_ID>" }
```
On success (HTTP 200), the response contains `queryId` (camelCase) — the ID used for polling:
```python
query_id = response.json().get("queryId")
```

### Step 2 — Poll for results
```
GET https://app.coactive.ai/api/v1/queries/{query_id}
```
Poll every 2 seconds until `response["status"] == "Complete"`.

Possible status values: `Queued`, `Running`, `Stopping`, `Stopped`, `Complete`, `Failed`

Results are extracted from:
```python
result["result"]["data"][0]["data"]  # dict of column names → values for each row
```

Full confirmed response structure:
```python
{
  "data": [
    {
      "row": 0,
      "data": {
        "coactive_image_id": "...",
        "coactive_video_id": "...",
        "olympics_games_now_prob": 0.002656,
        "olympics_games_now": 0,
        # ... all other columns
      }
    }
  ],
  "meta": { "page": { "total": 1, ... } },
  "error": None
}
```

For schema discovery, column names are extracted from the keys of `response["data"][0]["data"]`.

### Pagination
For large result sets, pagination is handled at the **SQL level** using `LIMIT` and `OFFSET` inside the query itself. The outer loop increments `offset` by the page size until the returned batch has fewer rows than the limit:

```python
limit = 10000
offset = 0
continue_processing = True
all_results = []

while continue_processing:
    query = f"SELECT ... FROM coactive_table_adv LIMIT {limit} OFFSET {offset};"
    # submit query → poll → extract records
    records_df = pd.DataFrame(records)
    all_results.append(records_df)
    offset += 10000
    if records_df.shape[0] < 10000:
        continue_processing = False
```

> Note: For aggregation queries (COUNT, SUM, AVG, GROUP BY), pagination is not needed — the result is always a small summary table.

---

## SQL Rules for the Agent

These rules must be followed when generating SQL for Coactive.

### Counting rules
Because `coactive_table_adv` has **one row per keyframe**, never use `COUNT(*)` to count videos, shots, or images. Always use `COUNT(DISTINCT ...)`:

| User asks about | Correct SQL |
|---|---|
| Number of videos | `COUNT(DISTINCT coactive_video_id)` |
| Number of shots | `COUNT(DISTINCT coactive_shot_id)` |
| Number of images/keyframes | `COUNT(DISTINCT coactive_image_id)` |

### Threshold rules
- Always use `_prob` columns for threshold comparisons, not the binary column
- The binary column uses a fixed default threshold of 0.7 — it is not flexible
- Let the user's question guide the threshold; default to 0.5 if not specified

### General rules
- Use CTEs for multi-step queries
- Use `MAX(coactive_image_id)` as the representative image when grouping by video or shot
- Only use columns that exist in the discovered schema
- Never use `SELECT *` in final queries — select only relevant columns
- Return only valid SQL — no explanation, no markdown, no code fences

---

## SQL Query Examples

### 1. Count distinct videos in the dataset
```sql
SELECT COUNT(DISTINCT coactive_video_id) AS total_videos
FROM coactive_table_adv;
```

### 2. Get min/max probability for a concept
```sql
SELECT
  MIN(slam_dunk_prob) AS min_prob,
  MAX(slam_dunk_prob) AS max_prob
FROM coactive_table_adv;
```

### 3. Filter keyframes by concept probability threshold
```sql
SELECT
  slam_dunk_prob,
  keyframe_time_ms,
  coactive_video_id,
  coactive_image_id
FROM coactive_table_adv
WHERE slam_dunk_prob > 0.5
ORDER BY slam_dunk_prob DESC;
```

### 4. Retrieve concept occurrences over time (timeline)
```sql
WITH occurrences AS (
  SELECT
    coactive_video_id,
    keyframe_time_ms,
    slam_dunk_prob,
    MAX(coactive_image_id) AS coactive_image_id
  FROM coactive_table_adv
  WHERE slam_dunk_prob > 0.5
  GROUP BY coactive_video_id, keyframe_time_ms, slam_dunk_prob
)
SELECT
  o.coactive_video_id,
  o.keyframe_time_ms,
  o.slam_dunk_prob,
  o.coactive_image_id
FROM occurrences o
ORDER BY o.coactive_video_id, o.keyframe_time_ms ASC;
```

### 5. Count labeled frames per video with min/max probability
```sql
WITH occurrences AS (
  SELECT
    coactive_video_id,
    COUNT(*) AS occurrence_count,
    MAX(coactive_image_id) AS coactive_image_id,
    MAX(slam_dunk_prob) AS max_probability,
    MIN(slam_dunk_prob) AS min_probability
  FROM coactive_table_adv
  WHERE slam_dunk_prob > 0.1
  GROUP BY coactive_video_id
)
SELECT
  o.max_probability,
  o.min_probability,
  o.occurrence_count,
  o.coactive_video_id,
  o.coactive_image_id
FROM occurrences o
ORDER BY o.occurrence_count DESC;
```

### 6. Calculate concept probabilities as percentages
```sql
WITH concept AS (
  SELECT
    coactive_image_id,
    slam_dunk_prob AS concept_probability
  FROM coactive_table_adv
)
SELECT
  coactive_image_id,
  concept_probability,
  CONCAT(ROUND(concept_probability * 100), '%') AS concept_percentage
FROM concept
WHERE concept_probability > 0.50
ORDER BY concept_probability DESC;
```

### 7. Video-level metadata generation (K-keyframe tagging)
Tag videos where K or more keyframes have a concept probability above threshold T.
```sql
WITH video_level_tab AS (
  SELECT
    coactive_video_id,
    SUM(CASE WHEN slam_dunk_prob > 0.5 THEN 1 ELSE 0 END) AS num_labeled_kfs
  FROM coactive_table_adv
  GROUP BY coactive_video_id
)
SELECT
  *,
  CASE WHEN num_labeled_kfs >= 3 THEN 1 ELSE 0 END AS slam_dunk_tag
FROM video_level_tab
ORDER BY num_labeled_kfs DESC;
```

### 8. Average number of images per video with concept above threshold
```sql
WITH per_video AS (
  SELECT
    coactive_video_id,
    COUNT(DISTINCT coactive_image_id) AS image_count
  FROM coactive_table_adv
  WHERE slam_dunk_prob > 0.5
  GROUP BY coactive_video_id
)
SELECT AVG(image_count) AS avg_images_per_video
FROM per_video;
```

---

## Dataset Reference

| Config | Value |
|---|---|
| Default Dataset ID | `bb909094-21ba-49b4-863f-ac5edb9af0b6` |
| Primary Table | `coactive_table_adv` |
| API Base URL | `https://api.coactive.ai/api/v1` |

> Note: The dataset ID is provided at runtime by the user. The default above is for reference only.
