# NL-SQL Agent for Coactive

An AI-powered agent that converts natural language questions into SQL queries and executes them against the Coactive visual analytics platform.

> Type a question in plain English → get real data back from your video/image dataset.

---

## What It Does

- Accepts a natural language question from the user
- Sends it to the OpenAI API with the Coactive table schema as context
- Receives a SQL query targeting Coactive tables
- Executes that query via the Coactive API (async: submit → poll → retrieve)
- Returns the results in a readable format
- Logs every interaction (timestamp, input, generated SQL, result summary, any errors)

---

## Stack

| Layer    | Technology                  |
|----------|-----------------------------|
| Agent    | OpenAI API (GPT-4)          |
| Backend  | FastAPI                     |
| Database | Coactive API                |
| Frontend | Vanilla JS (single HTML file)|
| Logging  | JSON file                   |

---

## Coactive Data Source

| Config        | Value                                  |
|---------------|----------------------------------------|
| Dataset ID    | `bb909094-21ba-49b4-863f-ac5edb9af0b6` |
| Primary Table | `coactive_table_adv`                   |
| API Base URL  | `https://app.coactive.ai/api/v1`       |

### Primary Table Schema: `coactive_table_adv`

An advanced keyframe-level table with concept probabilities and metadata.

| Column               | Definition                                      | Format  |
|----------------------|-------------------------------------------------|---------|
| keyframe_index       | Index of the keyframe within the asset          | string  |
| coactive_shot_id     | Coactive shot identifier                        | string  |
| coactive_video_id    | Coactive video identifier                       | string  |
| coactive_image_id    | Coactive image/keyframe identifier              | string  |
| path                 | Storage path of the keyframe                    | string  |
| created_dt           | Timestamp of video ingestion                    | timestamp |
| keyframe_time_ms     | Start time of the keyframe                      | float   |
| concept_column       | Binary flag per concept (e.g. slam_dunk)        | double  |
| concept_probability  | Likelihood score per concept (e.g. slam_dunk_prob) | double |

---

## Project Structure

```
nl-sql-agent/
├── agent/              # AI agent logic (NL → SQL → Coactive execution)
│   ├── agent.py        # Main loop
│   ├── prompt.py       # Prompt builder with schema injection
│   └── schema.py       # Coactive schema definitions (static, from docs)
├── backend/            # FastAPI app (API endpoints)
├── frontend/           # Single-page UI
├── data/               # Reserved for local test fixtures if needed
├── logs/               # Interaction logs (JSON file)
├── tests/              # Tests
├── .env                # Secrets — never committed
├── .env.example        # Template for required env vars
├── requirements.txt
└── README.md
```

---

## Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key
COACTIVE_CLIENT_ID=your_client_id
COACTIVE_CLIENT_SECRET=your_client_secret
COACTIVE_DATASET_ID=bb909094-21ba-49b4-863f-ac5edb9af0b6
```

---

## Setup (Local)

> Full setup instructions will be completed on Day 3. Skeleton below.

### Prerequisites
- Python 3.10+
- OpenAI API key
- Coactive account with CLIENT_ID and CLIENT_SECRET

### Steps
```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/nl-sql-agent.git
cd nl-sql-agent

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Fill in your API keys in .env

# 5. Run the agent (terminal)
python agent/agent.py
```

---

## API Endpoints

> To be completed on Day 2.

| Method | Endpoint  | Description                        |
|--------|-----------|------------------------------------|
| POST   | `/query`  | Send a natural language question   |
| GET    | `/logs`   | Retrieve interaction history       |

---

## 3-Day Build Plan

| Day | Theme                        | Goal                                                        |
|-----|------------------------------|-------------------------------------------------------------|
| 1   | Foundation & Core Agent Loop | Terminal input → SQL → Coactive API → real result           |
| 2   | Backend + Minimal Frontend   | Browser UI → FastAPI → agent → results table                |
| 3   | Hardening & Docs             | Error handling, logs UI, README, CI                         |

---

## Known Limitations

> To be filled in on Day 3 after end-to-end testing.

---

## Backlog (v2 Ideas)

> To be filled in on Day 3.
