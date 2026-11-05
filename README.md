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
User input (CLI or web UI)
  -> Tavily Search API, 4 category queries, last 30 days
  -> Parse published_date (ISO and RFC/GMT formats)
  -> Filter: drop dated results outside the window
  -> Deduplicate by normalised URL (www and trailing slash ignored)
  -> Sort: newest first, undated last and flagged "date unknown"
  -> Summarise: extractive fallback, or LLM only if LLM_API_KEY is set
  -> Render: Markdown and PDF, same content
```

Files:

- `main.py`: CLI entry point
- `web_ui.py`: simple web UI, Python standard library only, no extra framework
- `tavily_agent/dates.py`: date parsing and the 30-day window
- `tavily_agent/tavily_client.py`: Tavily API client
- `tavily_agent/briefing.py`: filter, dedupe, sort, briefing builder
- `tavily_agent/summarizer.py`: extractive fallback plus optional LLM summary
- `tavily_agent/render.py`: Markdown and PDF rendering
- `live_briefing.py`: live runner, reuses the same pipeline
- `build_playground_briefings.py`: builds the live briefings from the
  transcribed Tavily Playground results in `examples/live-playground-2026-11-05.json`
- `tests/test_briefing.py`: offline unit tests
- `examples/fixtures.json`: clearly labelled test fixtures, NOT real data
- `examples/sample_briefing.md` and `examples/sample_briefing.pdf`: sample output from fixtures
- `examples/live-openai/`, `examples/live-google/`, `examples/live-microsoft/`:
  real live briefings, Markdown and PDF, built Nov 5, 2026 (see below)

## Install

```bash
pip install -r requirements.txt
```

Requirements are only `requests` and `reportlab`. The web UI uses
only the Python standard library, so it runs without Streamlit or
FastAPI. That choice was made for robustness: fewer dependencies,
fewer ways for the demo to fail.

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

```bash
python3 web_ui.py --port 8000
```

Then open http://127.0.0.1:8000 in a browser. Tick "Mock mode" to
use fixtures, or leave it unticked for live mode (needs
`TAVILY_API_KEY` set when the server starts).

## How AI is used

- Tavily Search is the research layer: it finds and ranks real web
  results with relevance scores and snippets.
- Summarisation is extractive by default: the summary reuses the
  first sentence of the top result snippets and counts results by
  category. No new facts are created.
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
for the web UI and tests. No database, no paid service beyond the
Tavily API itself.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

12 tests, all offline: date parsing, window boundaries, old-result
filtering, deduplication, sorting, briefing formatting, empty
results, and a full fixture pipeline run.
