# QE AgentX — VW Release Validation and Quality Engineering Platform

> **Sogeti QualityForward AI Hackathon 2026 | Track: Test Design & Generation**

Transform a Jira user story into a complete, traceable test suite in under **90 seconds**.
Validate a Volkswagen Feature App release, generate a complete traceable test suite, and produce a risk-based release recommendation while keeping manual QA execution under human control.

See [RELEASE_VALIDATION_ARCHITECTURE.md](RELEASE_VALIDATION_ARCHITECTURE.md) for the workflow, API contract, and deployment boundaries.

---

## Quick Start

### 1. Clone & Setup

```bash
cd qe_agentx
cp .env.example .env
# OPTIONAL: Fill in your Azure OpenAI and Jira credentials in .env
# If not configured, QE AgentX will automatically run in Mock Mode (see below)
pip install -r requirements.txt
```

### 2. Run the Demo — Mock Mode (No Azure Credentials Required)

```bash
python demo_runner.py
```

**Mock Mode automatically activates if Azure credentials are missing.**

The demo:

**No Azure setup required for hackathon judges or quick demos.**

### 3. Run with Production Azure OpenAI (Optional)

If you have Azure OpenAI credentials:

```bash
# Edit .env and fill in:
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_KEY=<your-key>
JIRA_BASE_URL=https://<your-org>.atlassian.net
JIRA_EMAIL=<your-email>
JIRA_API_TOKEN=<your-token>

python demo_runner.py  # Now uses live GPT-4o inference
```

### 4. Start the Full Stack (Docker)

```bash
cd infra/docker
docker-compose up
```


### 5. Run Tests

```bash
pytest tests/unit -m unit -v
```


## Mock Mode — Demo Without Azure Credentials

### What is Mock Mode?

**Mock Mode** is an automatic fallback that activates when Azure OpenAI credentials are not configured. Instead of calling the real GPT-4o API, all agents return **realistic, deterministic mock responses** based on the NGWD6-50396 CMS story.

### When Mock Mode is Used

Mock Mode activates automatically if:

### What Mock Mode Provides

| Agent | Mock Output | Use Case |
|-------|------------|----------|
| **Requirement Agent** | Parses story → extracts 4 ACs, detects 1 ambiguity | Judges see structured requirement analysis |
| **Scenario Agent** | Builds behaviour tree → 11 scenario nodes (happy/alternate/boundary/negative) | Tests see full coverage blueprint |
| **Test Case Agent** | Generates 7 test cases with Gherkin, steps, and risk scores | Complete executable test suite |
| **Test Data Agent** | Synthesises 5 realistic data sets (valid/boundary/invalid) | All data dependencies provided |
| **Coverage Agent** | Calculates 86% AC coverage, flags 3 gaps | Traceability verified |
| **RTM Agent** | Builds 7-row RTM linking AC → Scenario → TC → Data | Full traceability matrix |
| **Review Agent** | Quality rubric: 88.5/100, 1 finding, 3 gaps | Quality assurance complete |

### Mock vs. Production Mode

```
MOCK MODE                          PRODUCTION MODE
├─ No Azure credentials            ├─ Azure credentials configured
├─ Agent responses: hardcoded       ├─ Agent responses: live GPT-4o
├─ Demo completes in: <10s          ├─ Demo completes in: ~60-90s
├─ Perfect for: judges, CI, quick   ├─ Perfect for: real use, accurate
│   testing                         │   domain analysis
└─ Output is: deterministic         └─ Output is: unique per story
```

### How to Activate Mock Mode

**Explicitly** (for guaranteed mock execution):
```bash
# Leave .env missing or empty
# Do not set AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT

python demo_runner.py
# Output: "⚠️  MOCK MODE ENABLED"
```

**Automatically** (default for demo):
```bash
# Just run the demo — it detects missing credentials
python demo_runner.py
```

### Example Mock Mode Output

```
============================================================
  QE AgentX — Hackathon Demo Runner
============================================================

⚠️  MOCK MODE ENABLED
   • No Azure OpenAI credentials detected
   • Using realistic mock responses for all agents
   • Demo results are deterministic and hardcoded

📋 Story: NGWD6-50396 — 🔵 [CMS][NBD'26] S127 Feature Cluster...
🔑 Run ID: a7f3e2b1

  ✅ Analysing Requirements
  ✅ Building Scenario Tree
  ✅ Generating Test Cases
  ✅ Synthesising Test Data
  ✅ Calculating Coverage
  ✅ Building RTM
  ✅ Reviewing Quality
  ✅ Generating Report

============================================================
  RESULTS
============================================================
  Test Cases Generated : 7
  AC Coverage          : 86.0%
  Quality Score        : 88/100
  RTM Rows             : 7
  Gaps Detected        : 3
  Errors               : 0

  Executive Summary:
  The NGWD6-50396 Feature Cluster Section story has been analysed 
  and a complete test suite of 7 test cases has been generated...

  📄 Markdown  → qe_agentx\demo_output\NGWD6-50396_testcases.md
  📦 Xray JSON → qe_agentx\demo_output\NGWD6-50396_xray.json
  📊 RTM CSV   → qe_agentx\demo_output\NGWD6-50396_rtm.csv
============================================================
```


```
Entry Layer     →   Streamlit UI / FastAPI / Jira Webhook
Orchestration   →   LangGraph State Machine (8-node pipeline)
Agent Layer     →   8 specialised agents (Requirement → Reporting)
AI Layer        →   Azure OpenAI GPT-4o + text-embedding-3-large
Integration     →   Jira REST API + Xray REST API
Export          →   Markdown | Xray JSON | RTM CSV
```

## Project Structure

```
qe_agentx/
├── agents/          8 LangChain agents
├── orchestrator/    LangGraph state machine + HITL routing
├── models/          Pydantic schemas for all pipeline artefacts
├── integrations/    Jira and Xray API clients
├── api/             FastAPI REST backend
├── ui/              Streamlit frontend
├── exports/         Markdown / JSON / CSV exporters
├── config/          Settings + prompt templates
├── tests/           Unit tests (mocked LLM)
├── infra/           Docker + Bicep IaC
└── demo_runner.py   Standalone hackathon demo
```

## Pipeline Flow

```
Jira Story
  │
  ▼
[1] Requirement Agent    → Structured Requirement Object (SRO)
  │                          + ambiguity detection
  ▼
[HITL Gate]              → QA engineer clarifies ambiguities
  │
  ▼
[2] Scenario Agent       → Behaviour Tree (happy/alternate/boundary/negative/NFR)
  │
  ▼
[3] Test Case Agent      → Test Cases with steps, risk scores, Gherkin
[4] Test Data Agent      → Domain-aware data sets (valid/boundary/invalid/null)
  │
  ▼
[5] Coverage Agent       → AC coverage map + gap detection
[6] RTM Agent            → Requirements Traceability Matrix
  │
  ▼
[7] Review Agent         → Quality rubric scoring + duplicate detection
  │
  ▼
[HITL Gate]              → Human approval if quality < 70
  │
  ▼
[8] Reporting Agent      → Final Report Bundle → Xray / Markdown / CSV
```

## Key Metrics (Demo Story: NGWD6-50396)

| Metric | Value |
|--------|-------|
| Manual effort estimate | ~6 hours |
| QE AgentX time | < 90 seconds |
| Test cases generated | 12–15 |
| AC coverage | 90%+ |
| Traceability | Real-time RTM |


*Built for Sogeti QualityForward AI Hackathon 2026*
