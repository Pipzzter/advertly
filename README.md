<div align="center">
  <a href="./frontend/public/advertly-logo.png">
    <img src="./frontend/public/advertly-logo.png" alt="Advertly logo" width="112" height="112">
  </a>
  <h1>Advertly</h1>
  <p>From raw copy to ready-to-publish advertorials.</p>
  <p><strong>For marketers and media buyers turning raw campaign copy into polished advertorial landing pages,<br>with structured sections, on-page layout, and contextual imagery generated automatically.</strong></p>
  <p><a href="#how-to-run-it"><strong>▶ Run Advertly locally</strong></a></p>
  <p><a href="#what-it-does">What it does</a> · <a href="#who-it-is-for">Who it's for</a> · <a href="#how-to-run-it">Run it</a> · <a href="#see-it-working">Walkthrough</a> · <a href="#how-the-ai-works">How the AI works</a> · <a href="#how-its-built">How it's built</a> · <a href="#does-it-hold-up">Tests</a></p>
  <p>
    <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white">
    <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi&logoColor=white">
    <img alt="Vue 3" src="https://img.shields.io/badge/Vue-3-42b883?style=flat-square&logo=vuedotjs&logoColor=white">
    <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat-square&logo=typescript&logoColor=white">
    <img alt="Gemini" src="https://img.shields.io/badge/Gemini-2.5%20Flash-8E75B2?style=flat-square&logo=googlegemini&logoColor=white">
    <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-black?style=flat-square">
  </p>
</div>

---

## What it does

Advertly turns a block of raw advertorial copy into a complete, styled landing page — no
pasting text into a template line by line, no hunting for stock photos.

Give it your copy (headline, hook, story, testimonials, offer…) and it:

- **Parses the copy into structured sections** with an LLM — headline, hook, introduction,
  body sections, product presentation, social proof, reviews, offer, and references.
- **Fills a clean HTML template** — cloning repeatable blocks (body sections, reviews,
  social proof) and dropping optional sections that have no content.
- **Generates a contextual image for every visual slot** — hero, body illustrations,
  product shot, reviewer portraits — embedded inline as base64 (no external files).
- **Returns one ready-to-publish HTML page** you can preview in the browser and download
  as a self-contained ZIP.

One paste in, one publishable advertorial out.

## Who it is for

- **Performance marketers and media buyers** producing advertorials at volume.
- **DTC and affiliate advertisers** who iterate on angles and need pages fast.
- **Agencies and freelancers** turning a copywriter's doc into a live page in minutes.
- Anyone who has strong copy but doesn't want to hand-build the page and source imagery.

If you've ever pasted copy into a template slot by slot and then gone looking for photos,
Advertly replaces that whole loop.

## How to run it

**Prerequisites:** Python 3.12+, Node.js 20+, and a Google Gemini API key. PostgreSQL is
optional — only the auth/user endpoints use it.

```bash
git clone https://github.com/Pipzzter/advertly.git
cd advertly
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
cp .env.example .env             # then set GEMINI_API_KEY (and DB creds if needed)
alembic upgrade head             # optional: auth/user tables (requires PostgreSQL running)
uvicorn app.main:app --reload    # http://localhost:8000  ·  API docs at /api/v1/docs
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev                      # http://localhost:5173
```

The dev server proxies `/api` to the backend at `http://127.0.0.1:8000`; set
`API_PROXY_TARGET` to point it somewhere else.

### Or with Docker

```bash
cd docker
docker compose up --build        # backend + frontend + PostgreSQL
```

> **Environment:** copy `backend/.env.example` → `backend/.env` and set at least
> `GEMINI_API_KEY`. The app boots without a live database (the copy generator doesn't need
> one), but auth/user features and `alembic upgrade head` require PostgreSQL.

## See it working

**In the app:**

1. Open `http://localhost:5173` and choose **Page Generator**.
2. Pick a **template** from the dropdown and paste your **raw marketing copy**.
3. Generate. Advertly parses the copy, fills the template, and generates the images.
4. **Preview** the finished page inline, then **download it as a ZIP**.

**Under the hood** — it's a single API call:

```http
POST /api/v1/agents/copyinjection
Content-Type: application/json

{
  "template_id": "template_simple",
  "raw_copy": "Doctors Stunned: The 5-Second Morning Habit… [your full advertorial]",
  "product_name": "CalmLeaf",
  "product_category": "Sleep & Wellness"
}
```

```json
{
  "html": "<!doctype html> … complete page with inline images …",
  "placeholders_found": ["[Headline goes here]", "[Hook goes here]", "…"],
  "placements": [{ "placeholder": "[Headline goes here]", "content_preview": "…" }],
  "images_generated": 9,
  "success": true
}
```

The returned `html` is self-contained (images are inline base64 data URIs), so preview and
ZIP packaging happen entirely client-side.

## How the AI works

Advertly is built around a small, extensible **agent architecture**. It ships one agent
today — the **Copy Injection Agent** — which orchestrates a six-step pipeline:

1. **Load template** — read the HTML plus metadata describing which sections repeat, which
   are optional, and what placeholders exist.
2. **Parse copy (LLM)** — a single call to **Gemini 2.5 Flash** with *structured output*.
   The model returns a typed `ParsedCopy` object (Pydantic), not free text: headline, hook,
   intro, 3–5 body sections, product presentation, unique social proofs, a case study,
   human-sounding reviews, an offer, and references. The JSON schema is derived from the
   Pydantic model (`response_json_schema`), so the result is validated on arrival.
3. **Fill repeatable sections** — clone the body / review / social-proof blocks once per
   parsed item, regenerating element IDs to avoid collisions.
4. **Fill simple placeholders** — headline, hook, author, date, offer, and so on, with
   sensible fallbacks for required slots.
5. **Prune and generate images** — remove optional sections that have no content, then
   generate one image per visual slot with **Gemini 2.5 Flash Image** ("Nano Banana"),
   embedded inline as base64 data URIs.
6. **Clean up** — strip any placeholder that wasn't filled, so the output is always valid.

Two ideas keep it reliable:

- **The LLM does semantic extraction; deterministic code does assembly.** The model never
  touches HTML structure — it only categorizes copy into typed fields. All templating,
  cloning, and cleanup is plain, testable Python. Layouts stay stable and debuggable.
- **Purpose-built image prompts.** Each image type has its own system prompt tuned for
  advertorials — headline images create curiosity, body images explain one idea simply,
  product images show the mechanism — so results read editorial, not stock-photo.

Both the text and image clients run **async with exponential-backoff retries** on
rate-limit and transient errors (429 / 503 / timeouts). Adding a second agent means
subclassing `BaseAgent[Input, Output]` and registering a router — the frontend agent
registry picks it up automatically.

> **Models:** `gemini-2.5-flash` (copy parsing, structured JSON) and
> `gemini-2.5-flash-image` (image generation). See [`docs/PAGE_GENERATOR.md`](docs/PAGE_GENERATOR.md)
> for the full agent deep-dive and [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md)
> for the high-level flow.

## How it's built

**Backend** — Python 3.12 · FastAPI · SQLAlchemy 2 (async) + PostgreSQL · Alembic ·
Pydantic v2 · google-genai · JWT auth (argon2) · pytest
**Frontend** — Vue 3 (Composition API) · TypeScript · Vite · Pinia · Vue Router ·
Tailwind CSS v4 · JSZip (client-side packaging)
**Infrastructure** — Docker + Docker Compose (backend, frontend/nginx, PostgreSQL)

```
advertly/
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/           # auth, user, health, copy_injection
│   │   ├── core/                     # config, security, logging
│   │   ├── db/                       # async session, base
│   │   ├── models/ · schemas/        # SQLAlchemy models · Pydantic schemas
│   │   ├── services/
│   │   │   └── agents/               # AI agents
│   │   │       ├── base.py           # abstract BaseAgent[Input, Output]
│   │   │       ├── llm_client.py     # Gemini text client (structured output)
│   │   │       ├── image_client.py   # Gemini image client (Nano Banana)
│   │   │       └── copy_injection/   # Copy Injection Agent (parse → fill → images)
│   │   └── static/templates/         # HTML template + metadata
│   ├── alembic/                      # database migrations
│   └── tests/                        # pytest suite
├── frontend/                         # Vue 3 + Vite SPA
├── docker/                           # Dockerfiles + docker-compose
└── docs/                             # architecture & agent deep-dive
```

**Design notes:** an agent pattern for extensibility · structured LLM output for
reliability · client-side preview and ZIP so the server stays stateless about generated
files · a layered backend (api / services / agents / db / schemas).

## Does it hold up

- **28 backend tests** (pytest, async) covering auth, users, health, schemas, and services.
- The suite runs against an **in-memory SQLite** database with strict pytest config — **no
  live database and no Gemini calls required**, so it's CI-friendly.
- The **frontend is fully type-checked** with `vue-tsc`.

```bash
# backend
cd backend && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pytest -q                                 # 28 passed

# frontend
cd frontend
npm run type-check
npm run build
```

## License

MIT
