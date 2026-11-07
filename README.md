# Tavily Research Agent

A pre-meeting briefing agent for the Geek Room Global AI Hackathon.
Theme: Tavily Research Agent (Tavily-primary).

## Problem

People go into meetings unprepared. Searching for what a company or
person did in the last 30 days takes too long, and AI answers often
mix old news with new news, with no sources to check.

## Solution

Type a company or person name and a meeting date. The app searches
Tavily for the last 30 days only, in four categories, news, launches
and product updates, hires and leadership, and funding, deals and
partnerships. It returns a one-page briefing with:

- A short summary
- Key developments, each with a date and a source link
- 3 to 5 discussion points
- 3 to 5 open questions

No invented facts: every development comes from a Tavily result and
carries its source URL. If there are no results, the briefing says so
clearly and lists nothing.

## Architecture

```
User input (CLI, standard library web UI, or Streamlit web UI)
  -> Tavily Search API, 4 category queries, last 30 days
  -> Parse published_date (ISO and RFC/GMT formats)
  -> Filter: drop dated results outside the window
  -> Deduplicate by normalised URL (www and trailing slash ignored)
  -> Sort: newest first, undated last and flagged "date unknown"
  -> Summarise: relevance-aware extractive fallback, or LLM only if LLM_API_KEY is set
  -> Render: Markdown and PDF, same content
```

Files:

- `main.py`: CLI entry point
- `web_ui.py`: simple web UI, Python standard library only, no extra framework
- `app.py`: Streamlit web UI, same pipeline, optional (needs `streamlit`)
- `tavily_agent/dates.py`: date parsing and the 30-day window
- `tavily_agent/tavily_client.py`: Tavily API client
- `tavily_agent/briefing.py`: filter, dedupe, sort, briefing builder
- `tavily_agent/summarizer.py`: extractive fallback plus optional LLM summary
- `tavily_agent/ui_helpers.py`: shared input validation and display shaping for both web UIs
- `tavily_agent/render.py`: Markdown and PDF rendering
- `live_briefing.py`: live runner, reuses the same pipeline
- `build_playground_briefings.py`: builds the live briefings from the
  transcribed Tavily Playground results in `examples/live-playground-2026-11-05.json`
- `build_pitch_deck.py`: rebuilds the pitch deck (PDF and PPTX) from one slide list
- `.github/workflows/ci.yml`: GitHub Actions, runs the unit tests on Python 3.12
- `tests/test_briefing.py` and `tests/test_streamlit_ui.py`: offline unit tests
- `examples/fixtures.json`: clearly labelled test fixtures, NOT real data
- `examples/sample_briefing.md` and `examples/sample_briefing.pdf`: sample output from fixtures
- `examples/live-openai/`, `examples/live-google/`, `examples/live-microsoft/`:
  real live briefings, Markdown and PDF, built Nov 5, 2026 (see below)

## Install

```bash
pip install -r requirements.txt
```

Requirements are `requests` and `reportlab`, plus `streamlit` as an
optional dependency for the Streamlit web UI only. The standard
library web UI and the CLI run without Streamlit. That choice was
made for robustness: fewer dependencies, fewer ways for the demo
to fail.

## Run, mock mode (no key, no network)

```bash
python3 main.py --subject "Example Company" --meeting 2026-11-10 --mock --out examples/sample_briefing
```

This writes `examples/sample_briefing.md` and `examples/sample_briefing.pdf`.
The fixtures are invented samples for testing the pipeline. They are
labelled as fixtures in `examples/fixtures.json` and must never be
presented as live Tavily results.

## Run, live mode

1. Get a Tavily API key at https://app.tavily.com/home
2. Hackathon participants were given coupon code GEEKROOM2 for 8000
   Tavily credits, redeemable before November 28, 2026, per the
   resources list supplied for this hackathon. Claiming credits is
   done in your own browser, not by this app.
3. Set the key only as an environment variable:

```bash
export TAVILY_API_KEY="your-key-here"
python3 main.py --subject "Acme Corp" --meeting 2026-11-10 --out examples/acme
```

Never put a real key in source code, in a committed `.env` file, or
in a chat message. `.env.example` lists only variable names.
`.gitignore` excludes `.env`.

## Live results, Nov 5, 2026

Real Tavily data, gathered in the Tavily API Playground on Nov 5,
2026 (12 searches: 4 categories x 3 companies, 5 results each, 60
total, meeting date 2026-11-05, window 2026-10-06 to 2026-11-05),
transcribed exactly as shown into
`examples/live-playground-2026-11-05.json` and built through the
existing pipeline by `build_playground_briefings.py`.

| Company | Kept | Dropped as truncated URL | Dropped as profile page | Dropped as duplicates | Dropped as too old |
|---|---|---|---|---|---|
| OpenAI | 14 | 1 | 3 | 2 | 0 |
| Google | 15 | 5 | 0 | 0 | 0 |
| Microsoft | 8 | 10 | 2 | 0 | 0 |
| Total | 37 | 16 | 5 | 2 | 0 |

Outputs, each labelled LIVE via Tavily Playground with a source and
truncation note:

- `examples/live-openai/briefing.md` and `briefing.pdf` (14 kept)
- `examples/live-google/briefing.md` and `briefing.pdf` (15 kept)
- `examples/live-microsoft/briefing.md` and `briefing.pdf` (8 kept)

Relevance-aware summary (Batch 1, Nov 7, 2026): the Top findings
in each summary now use only developments that name the subject
in both their title and snippet. Developments that do not are
still listed in full, with source links, in Key developments, and
the briefing notes how many were left out of the summary: OpenAI
4, Google 11, Microsoft 4. Kept counts did not change (14, 15, 8).
This removed two off-topic snippets from the summaries: the
Learjet crash snippet from the Google summary, and the OpenAI
hires article from the Microsoft summary. The exclusions are
mostly driven by the truncated Playground snippets, which often
do not name the subject even when the title does. Full record:
`LIVE_TEST.md`, section "Relevance-aware summary, Batch 1,
2026-11-07".

Reproduce the live briefings from the transcribed results:

```bash
python3 build_playground_briefings.py
```

Honest limit, read this before judging: the Playground JSON view
truncates long snippets at about 100 characters and truncates some
long titles and URLs, so snippets in the live briefings are the
truncated extracts exactly as returned, never a fuller text.
Results whose source URL was truncated were dropped because the
link cannot be verified (16 of 60, which is why Microsoft kept
only 8), and Tavily knowledge-company profile pages were dropped
because they are profiles, not dated developments. The direct API
route from this environment still returns HTTP 401 with the stored
credential, while the same Tavily key works in the Playground, so
these briefings prove the pipeline on real Tavily data, not the
direct API client route (`live_briefing.py` is still unproven).
Full record: `LIVE_TEST.md`, section "LIVE VIA PLAYGROUND
2026-11-05".

## Run, web UI

Standard library UI (no extra framework):

```bash
python3 web_ui.py --port 8000
```

Then open http://127.0.0.1:8000 in a browser. Tick "Mock mode" to
use fixtures, or leave it unticked for live mode (needs
`TAVILY_API_KEY` set when the server starts).

Streamlit UI (needs `streamlit`, same pipeline, same briefings):

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints (usually
http://localhost:8501). Enter a company or person and a meeting
date, tick "Mock mode" for fixtures or leave it unticked for live
mode, and press "Build briefing". The briefing shows the summary,
kept and dropped counts, every development with its source link,
discussion points, open questions, and Markdown and PDF download
buttons. Both web UIs share the input validation and display
helpers in `tavily_agent/ui_helpers.py`.

## How AI is used

- Tavily Search is the research layer: it finds and ranks real web
  results with relevance scores and snippets.
- Summarisation is extractive by default: the summary reuses the
  first sentence of the top result snippets and counts results by
  category. No new facts are created.
- The summary is relevance-aware: a development is quoted in the
  Top findings only when the subject name appears in both its
  title and its snippet (case-insensitive, subject string only).
  Other kept developments stay in Key developments in full, with
  source links, and the briefing notes how many were left out of
  the summary.
- An LLM summary is used only if `LLM_API_KEY` is set. It is given
  only the supplied snippets and is told not to invent dates, facts,
  or sources. Any LLM failure falls back to the extractive summary,
  and the briefing labels which mode was used (`extractive` or `llm`).
- The LLM is never used to add new developments. Discussion points
  and open questions are templates filled with real finding titles
  and dates from the results.

## Tavily Search API, verified parameters

Verified on 2026-11-03 from https://docs.tavily.com and Tavily SDK
references linked from those docs. The official API reference page
fetched for this project showed the response shape but not the full
request schema, so parameters below are marked by source.

| Parameter | Value used | Source |
|---|---|---|
| Endpoint | POST https://api.tavily.com/search | Tavily docs and SDK references |
| Auth header | Authorization: Bearer <TAVILY_API_KEY> | Tavily docs and SDK references |
| Content-Type | application/json | Tavily docs and SDK references |
| query | Required, e.g. "Acme Corp news" | Tavily docs |
| topic | "news" for all four categories, to maximise published_date availability | Tavily docs, SDK reference |
| search_depth | "basic" by default, "advanced" with --search-depth advanced | Tavily docs |
| max_results | 5 by default, range 1 to 20 in docs | Tavily docs, SDK reference |
| time_range | "month" | Tavily docs |
| start_date, end_date | YYYY-MM-DD, computed as the 30 days before the meeting, capped at today | Tavily docs |
| include_domains, exclude_domains | Supported, not used by default | Tavily docs |
| include_answer, include_raw_content | False in this app, to keep output small and sourced | Tavily docs |
| Response results[] | title, url, content, score, published_date | Official API reference example, docs.tavily.com/documentation/api-reference/endpoint/search |

Unverified, and therefore NOT sent by this app:

- `include_published_date`: not confirmed on the official page
  fetched. The SDK notes published_date is tied to topic=news, so
  this app uses topic=news and handles a missing date explicitly
  instead of sending an unverified flag.
- Exact credit cost per depth: secondary sources report basic as
  1 credit and advanced as 2 credits, but that was not confirmed
  on the official page fetched, so it is not stated as fact here.

## Window rule, read this before judging a sample

The window is the 30 days before the meeting, capped at today.
If the meeting is in the future, the window ends today, because
future developments cannot be searched yet. Example: a meeting on
2026-11-10 run on 2026-11-03 gives the window 2026-10-04 to
2026-11-03. That is intentional and tested.

## Limitations

- Live mode through the direct API has NOT been proven yet: calls
  to api.tavily.com from this environment return HTTP 401 with the
  stored credential, while the same Tavily key works in the
  Playground. The Nov 5 live briefings above prove the pipeline on
  real Tavily data gathered in the Playground, not the direct API
  client route. See STATUS.md and LIVE_TEST.md.
- PDF rendering uses plain text, not Markdown, so development
  titles in the PDFs never show raw `**` markers. Verified by text
  extraction on all three live PDFs in Batch 1 (0 occurrences).
  The `**` markers seen in the demo video came from the on-screen
  Markdown list in one scene, not from the PDFs.
- If Tavily returns no published_date for a result, the briefing
  keeps it but flags it "date unknown". Its date could not be
  verified from Tavily alone, and the briefing says so.
- If one of the four category searches fails, the other three
  still run, and the failure is not hidden as a finding.
- The LLM summary path has NOT been tested live, because no LLM
  key was provided. The extractive fallback is the tested path.
- Bifrost is not used in this project. It was background only in
  the hackathon resources, and this submission is Tavily-primary,
  as the theme requires.

## Technologies

Python 3.12, requests, reportlab for PDF, Python standard library
for the web UI and tests, Streamlit as an optional UI, GitHub
Actions for CI (unit tests on Python 3.12, on push and pull
request). No database, no paid service beyond the Tavily API itself.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

23 tests, all offline: date parsing, window boundaries, old-result
filtering, deduplication, sorting, briefing formatting, empty
results, a full fixture pipeline run, relevance-aware summary
rules, and the Streamlit UI helpers (input validation and display
shaping). The two Streamlit app import tests run only when
Streamlit is installed, because it is an optional dependency.
