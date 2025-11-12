# README.md
<!-- filepath: /Users/harry/test/tt_jobot/jobot/README.md -->

# Jobot: AI-Powered Job Application Automation MVP

Jobot is a Python full-stack MVP for automating job discovery, resume tailoring, and application workflows. It leverages modern AI, browser automation, and workflow orchestration to streamline the job search and application process, with a human-in-the-loop for critical steps.

## Features

- **Job Discovery**: Automated job scraping from Seek and LinkedIn using Playwright and MCP servers.
- **Semantic Matching**: Uses vector embeddings (pgvector) and rule-based filtering to match jobs to your profile.
- **Resume Parsing & Tailoring**: Parses resumes with Unstructured, generates ATS-friendly versions tailored to each job using LLMs.
- **Workflow Orchestration**: Temporal workflows manage the end-to-end process, including human approval via Slack.
- **Notifications**: Slack and Email integration for job alerts and workflow actions.
- **Storage**: Uses PostgreSQL (with pgvector) for data and MinIO for file storage.

## Tech Stack

- **Backend**: FastAPI, Temporal Python SDK, SQLAlchemy, Alembic
- **Automation**: Playwright Python, MCP Python SDK
- **AI/LLM**: ScrapeGraphAI, Unstructured, OpenAI API (configurable)
- **Vector Search**: pgvector
- **Notifications**: Slack SDK, SMTP/SendGrid
- **Storage**: PostgreSQL, MinIO (S3-compatible)
- **Containerization**: Docker, docker-compose

## Directory Structure

```
jobot/
  apps/
    api/               # FastAPI REST/Webhook API
    workers/           # Temporal workers (activities/workflows)
    mcp_servers/
      seek/            # MCP server: Seek login/scrape/details
      linkedin/        # MCP server: LinkedIn login/scrape
      notifier/        # MCP server: Slack/Email notifications
      resume/          # MCP server: Resume parsing/export
  core/
    models/            # SQLAlchemy models & Alembic migrations
    embeddings/        # Embedding utilities
    templates/         # Email/cover letter templates
    prompts/           # LLM prompt templates
  infra/
    docker/            # Dockerfiles
    migrations/
  configs/
    config.yaml        # App configuration
  scripts/
    seed_demo_data.py
  docker-compose.yml
  pyproject.toml
  README.md
```

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/jobot.git
   cd jobot
   ```

2. **Configure environment variables**

   Copy `.env.example` to `.env` and fill in required secrets (LLM, Slack, SMTP, etc).

3. **Start services**

   ```bash
   docker compose up --build
   ```

4. **Install Playwright browsers (first time only)**

   ```bash
   docker compose exec api playwright install
   ```

5. **Run database migrations**

   ```bash
   docker compose exec api alembic upgrade head
   ```

6. **Seed demo data (optional)**

   ```bash
   docker compose exec api python scripts/seed_demo_data.py
   ```

## Example: MCP Server (Seek)

```python
from mcp.server import Server, tool
from playwright.sync_api import sync_playwright

app = Server(name="seek")

@tool()
def search_jobs(query: str, location: str = "Melbourne"):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state="secrets/seek.cookies.json")
        page = ctx.new_page()
        page.goto("https://www.seek.com.au/")
        # ...scrape jobs...
        return [{"title": "...", "company": "...", "url": "...", "jd_text": "..."}]
```

## Example: Temporal Workflow

```python
from temporalio import workflow, activity

@activity.defn
async def fetch_and_rank(keyword: str) -> list[dict]:
    # ...fetch jobs, rank by embedding...
    return ranked_jobs

@workflow.defn
class DiscoverJobs:
    @workflow.run
    async def run(self, keyword: str):
        jobs = await workflow.execute_activity(fetch_and_rank, keyword)
        # ...notify via Slack, wait for user action...
```

## License

This project is for educational and research purposes. Please comply with the Terms of Service and privacy policies of all third-party sites and APIs.

---
```# README.md
<!-- filepath: /Users/harry/test/tt_jobot/jobot/README.md -->

# Jobot: AI-Powered Job Application Automation MVP

Jobot is a Python full-stack MVP for automating job discovery, resume tailoring, and application workflows. It leverages modern AI, browser automation, and workflow orchestration to streamline the job search and application process, with a human-in-the-loop for critical steps.

## Features

- **Job Discovery**: Automated job scraping from Seek and LinkedIn using Playwright and MCP servers.
- **Semantic Matching**: Uses vector embeddings (pgvector) and rule-based filtering to match jobs to your profile.
- **Resume Parsing & Tailoring**: Parses resumes with Unstructured, generates ATS-friendly versions tailored to each job using LLMs.
- **Workflow Orchestration**: Temporal workflows manage the end-to-end process, including human approval via Slack.
- **Notifications**: Slack and Email integration for job alerts and workflow actions.
- **Storage**: Uses PostgreSQL (with pgvector) for data and MinIO for file storage.

## Tech Stack

- **Backend**: FastAPI, Temporal Python SDK, SQLAlchemy, Alembic
- **Automation**: Playwright Python, MCP Python SDK
- **AI/LLM**: ScrapeGraphAI, Unstructured, OpenAI API (configurable)
- **Vector Search**: pgvector
- **Notifications**: Slack SDK, SMTP/SendGrid
- **Storage**: PostgreSQL, MinIO (S3-compatible)
- **Containerization**: Docker, docker-compose

## Directory Structure

```
jobot/
  apps/
    api/               # FastAPI REST/Webhook API
    workers/           # Temporal workers (activities/workflows)
    mcp_servers/
      seek/            # MCP server: Seek login/scrape/details
      linkedin/        # MCP server: LinkedIn login/scrape
      notifier/        # MCP server: Slack/Email notifications
      resume/          # MCP server: Resume parsing/export
  core/
    models/            # SQLAlchemy models & Alembic migrations
    embeddings/        # Embedding utilities
    templates/         # Email/cover letter templates
    prompts/           # LLM prompt templates
  infra/
    docker/            # Dockerfiles
    migrations/
  configs/
    config.yaml        # App configuration
  scripts/
    seed_demo_data.py
  docker-compose.yml
  pyproject.toml
  README.md
```

## Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/jobot.git
   cd jobot
   ```

2. **Configure environment variables**

   Copy `.env.example` to `.env` and fill in required secrets (LLM, Slack, SMTP, etc).

3. **Start services**

   ```bash
   docker compose up --build
   ```

4. **Install Playwright browsers (first time only)**

   ```bash
   docker compose exec api playwright install
   ```

5. **Run database migrations**

   ```bash
   docker compose exec api alembic upgrade head
   ```

6. **Seed demo data (optional)**

   ```bash
   docker compose exec api python scripts/seed_demo_data.py
   ```

## Example: MCP Server (Seek)

```python
from mcp.server import Server, tool
from playwright.sync_api import sync_playwright

app = Server(name="seek")

@tool()
def search_jobs(query: str, location: str = "Melbourne"):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(storage_state="secrets/seek.cookies.json")
        page = ctx.new_page()
        page.goto("https://www.seek.com.au/")
        # ...scrape jobs...
        return [{"title": "...", "company": "...", "url": "...", "jd_text": "..."}]
```

## Example: Temporal Workflow

```python
from temporalio import workflow, activity

@activity.defn
async def fetch_and_rank(keyword: str) -> list[dict]:
    # ...fetch jobs, rank by embedding...
    return ranked_jobs

@workflow.defn
class DiscoverJobs:
    @workflow.run
    async def run(self, keyword: str):
        jobs = await workflow.execute_activity(fetch_and_rank, keyword)
        # ...notify via Slack, wait for user action...
```

## License

This project is for educational and research purposes. Please comply with the Terms of Service and privacy policies of all third-party sites and APIs.

---