# VentureCheck — Startup Idea Validator Bot

A browser-based GenAI application that turns a startup idea into a structured hypothesis review, highlights uncertain assumptions, and proposes evidence-gathering experiments.

## Important distinction

An AI cannot prove that a market exists. This project never invents market size, customer interviews, competitors, traction, or revenue. Its score measures how clearly the hypothesis is described—not whether the startup will succeed.

## Features

- Five-dimension idea score from 0–100
- Problem, customer, solution, revenue, and differentiation review
- Critical assumptions and risk identification
- Customer-interview, landing-page, and concierge-pilot experiments
- Offline deterministic demo mode
- Optional OpenAI Responses API mode
- Dependency-free Python web application
- Automated tests and CI workflow

## Deploy online

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Avanthika-2104/Startup-idea-validator-bot)

The included `render.yaml` creates a free Python web service in Render's Singapore region, runs the automated tests during the build, starts the app on Render's assigned port, and checks `/health`.

Render's free service can sleep after 15 minutes without traffic, so the first visit after a quiet period can take about one minute to load.

## Run

```bash
python app.py
```

Open `http://127.0.0.1:8002`.

### OpenAI mode

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="gpt-5.6-luna"
python app.py
```

Keep API keys outside the repository.

## Test

```bash
python -m unittest discover -s tests -v
```

## Architecture

```text
Idea form -> validation layer -> offline scorer or Responses API -> schema checks -> evidence plan
```

## Honest project status

The complete UI, offline evaluation, API integration layer, and tests work locally. Genuine model-generated analysis requires API access supplied by the person running the application.

The public deployment should initially use offline mode. Do not add an OpenAI key to a public demo without authentication, rate limits, and a spending limit.
