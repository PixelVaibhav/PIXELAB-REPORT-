---
title: Pixelab Report
emoji: 🩺
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Pixelab Report

Upload a medical report, phone photo, scanned PDF, scan image or DICOM file and get a plain-language explanation.

## Run locally
```
pip install -r requirements.txt
cp .env.example .env     # add your GEMINI_API_KEY
uvicorn main:app --reload
```

## Publish free on Hugging Face Spaces
1. Get a Gemini API key at https://aistudio.google.com/apikey
2. Create a Space at https://huggingface.co/new-space → SDK **Docker** → Blank → Public.
3. Upload every file in this folder (keep `static/index.html` inside `static/`).
4. Space → Settings → Variables and secrets → New **secret** named `GEMINI_API_KEY`.
5. Wait for the build. Your site is live at `https://<username>-<space-name>.hf.space`.

Free Spaces sleep when idle and wake on the next visit. Render, Koyeb or Google Cloud Run also work with this Dockerfile (use one instance only).

## Before real people use it
- Google's free Gemini tier may use submitted content to improve its products (check current terms). For medical data, use a key with billing enabled and update the privacy text in `static/index.html` to match.
- Set `RATE_LIMIT` so one visitor cannot use up your API quota.

## How it works
1. **Ingest:** PDFs, photos, DICOM and ZIPs become page images (rotated, contrast-enhanced when needed).
2. **Extract:** a vision model returns JSON per page, validated with Pydantic (`schemas.py`). Invalid rows are dropped and counted.
3. **Ground (RAG):** each lab test is matched to `kb/tests.json` by alias, then by embedding similarity (`rag.py`). Matched notes are the only source the explanation may use, and the UI shows which notes were used.
4. **Explain and highlight:** plain-language text plus highlights drawn on the original pages.

`kb/tests.json` holds short general-information notes written for this project. Review them, and add trusted sources and links, before real use.

## Tests, evaluation and metrics
- `python -m pytest` runs the offline unit tests.
- `python -m evaluation.make_samples` creates synthetic labelled reports. Add your own labelled cases in `evaluation/cases/`.
- `python -m evaluation.run_eval --models modelA,modelB` measures recall, value and status accuracy, latency and tokens per model.
- `GET /api/metrics` shows token use, errors and average latency. Set `PRICE_IN_PER_M` and `PRICE_OUT_PER_M` in `.env` to estimate cost. Logs never contain report text.
