# Tavily Research Agent

A pre-meeting briefing agent for the Geek Room Global AI Hackathon.
Theme: Tavily Research Agent (Tavily-primary).

## 30-second demo

1. Open the Streamlit app in Demo mode, no key needed.
2. Pick a prebuilt live briefing (OpenAI, Google, or Microsoft).
3. Read the summary, then open one source link to check it.

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
- `tavily_agent/tavily_client.py`: Tavily Search API client, with
  key hygiene (key trimmed, empty key rejected before any network
  call, one retry only on timeout, never on 401, clear error on 401)
- `tavily_agent/extract.py`: Tavily Extract API client, top 8 enrich only
- `tavily_agent/demo.py`: demo mode data for the Streamlit app,
  framework-free so it can be unit tested without Streamlit
- `tavily_agent/briefing.py`: filter, dedupe, sort, briefing builder
- `tavily_agent/summarizer.py`: extractive fallback plus optional LLM summary
- `tavily_agent/ui_helpers.py`: shared input validation and display shaping for both web UIs
- `tavily_agent/render.py`: Markdown and PDF rendering
- `live_briefing.py`: live runner, reuses the same pipeline
- `live_smoke.py`: one small live search, reports status only, writes no files
- `build_playground_briefings.py`: builds the live briefings from the
  transcribed Tavily Playground results in `examples/live-playground-2026-11-05.json`
  (`--enrich` adds Tavily Extract for the top 8 per company, off by default)
- `build_pitch_deck.py`: rebuilds the pitch deck (PDF and PPTX) from one slide list
- `.github/workflows/ci.yml`: GitHub Actions, runs the unit tests on Python 3.12
- `tests/test_briefing.py`, `tests/test_streamlit_ui.py`,
  `tests/test_live_client.py`, `tests/test_extract.py`,
  `tests/test_demo_mode.py`: offline unit tests, all HTTP mocked
- `examples/fixtures.json`: clearly labelled test fixtures, NOT real data
- `examples/sample_briefing.md` and `examples/sample_briefing.pdf`: sample output from fixtures
- `examples/live-openai/`, `examples/live-google/`, `examples/live-microsoft/`:
  real live briefings, Markdown and PDF, built Nov 5, 2026 (see below)

## Install

```bash
pip install -r requirements.txt
```

Requirements are `requests` and `reportlab`, plus `streamlit==1.67.0`
only for the Streamlit web UI. The version is pinned to 1.67.0,
verified as the latest release on pip on 2026-11-07, so a deploy
is not upgraded without notice. The standard library web UI and
the CLI run without Streamlit. That choice was made for
robustness: fewer dependencies, fewer ways for the demo to fail.

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

Key hygiene in the client (`tavily_agent/tavily_client.py`): the
key is trimmed of surrounding spaces, an empty key is rejected
before any network call, a search is retried once only on
timeout and never on 401, and a 401 raises a clear error that
names the fix (check the key in the Tavily dashboard, copy the
active default dev key, set it as `TAVILY_API_KEY`, never paste
it in chat or in code). The key value is never logged or shown
in an error. A key that does not start with `tvly-` only earns
a warning, because that prefix comes from a secondary source
and is unverified for this project. Check a fresh key first
with one small search that reports status only:

```bash
export TAVILY_API_KEY="your-key-here"
python3 live_smoke.py
```

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

Briefing quality, measured from the same live artefacts, is in
`QUALITY.md` (reproduce with `python3 quality_report.py`):
37 of 37 kept developments are dated, 37 of 37 carry a source
URL, and 18 of 37 name the subject in both title and snippet.

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
http://localhost:8501). It opens in Demo mode by default: pick
OpenAI, Google, or Microsoft and see the prebuilt live briefing
from Nov 5, 2026, with no Tavily call and no key used. Switch to
Live mode for a fresh briefing: enter your own Tavily key, which
is used for that session only, never stored and never written to
a file (use "Clear key" when done). If the app is deployed with
a key in Streamlit secrets, that is only a fallback when no
visitor key is entered. Mock mode runs with local fixtures and
needs no key. The briefing shows the summary, kept and dropped
counts, every development with its source link, discussion
points, open questions, and Markdown and PDF download buttons.
Both web UIs share the input validation and display helpers in
`tavily_agent/ui_helpers.py`.

Deploy (Streamlit Community Cloud, owner step, not done here):
push the repo to GitHub, then in the Streamlit workspace click
Create app, pick the repo, branch main, and `app.py`, and click
Deploy. Every push to main redeploys automatically. Secrets, if
wanted, go in the app settings, never into the repo: the file
`.streamlit/secrets.toml` is ignored by git and must never be
committed. The live link cannot be added to the locked
HackCulture form, only here in the README. Limits to expect:
the app sleeps after 12 hours without traffic, so a first visit
may show a wake-up screen first.

## Tavily Extract, full content for the top 8

The Playground snippets in the live briefings are truncated at
about 100 characters. Tavily Extract (`tavily_agent/extract.py`,
endpoint POST https://api.tavily.com/extract, verified from the
official docs 2026-11-07) can fetch the real page content for
the top 8 kept developments per company: URLs in batches of 20,
query set to the subject plus category, `chunks_per_source` 3,
basic depth, markdown format. The first extracted chunk (about
800 characters) is attached as full content, and the original
snippet, published date, and URL are kept unchanged. If Extract
fails for a URL, that URL is recorded in `failed_results` and
keeps its snippet as fallback. Extract does not return a
published date, so the date always comes from the search result.

Enriching is OFF by default. Turn it on with:

```bash
export TAVILY_API_KEY="your-key-here"
python3 build_playground_briefings.py --enrich
```

Cost, from the docs: basic depth is 1 credit per 5 successful
extractions, so enriching the 37 kept URLs costs about 8 credits
if all succeed. That is arithmetic from the documented per-5
cost, not a measured bill. Extract has not been run live yet:
the 401 key problem affects Extract the same way it affects
Search, and the tests use mocked HTTP only.

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
- Tavily Extract, off by default, can add the first extracted
  chunk of real page content to the top 8 kept developments per
  company, so the briefing is not limited to truncated snippets.
  The snippet, date, and URL are kept, and a failed extraction
  falls back to the snippet.
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
  client route. The Batch 2 client now trims the key, rejects an
  empty key before any network call, retries once only on timeout,
  and raises a clear 401 error naming the fix, all covered by
  mocked tests, but no live call has succeeded yet. See STATUS.md
  and LIVE_TEST.md.
- Tavily Extract has NOT been run live yet, for the same 401
  reason. The enrich path is code and mocked tests only, off by
  default, with the snippet kept as fallback.
- The Streamlit app has NOT been deployed yet. Demo mode is
  code and tests only; the deploy click needs a signed-in
  Streamlit account connected to GitHub, which is a parent step.
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
for the web UI and tests, Streamlit as an optional UI. No database,
no paid service beyond the Tavily API itself. A GitHub Actions CI
workflow file is ready locally at .github/workflows/ci.yml (unit
tests on Python 3.12, on push and pull request), pending upload
via the GitHub web UI, because the command line token lacks the
workflow scope to create it by push.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

74 tests, all offline: date parsing, window boundaries, old-result
filtering, deduplication, sorting, briefing formatting, empty
results, a full fixture pipeline run, relevance-aware summary
rules, the Streamlit UI helpers (input validation and display
shaping), direct API key hygiene with mocked HTTP (200, 401,
timeout retry, trimmed and empty keys), Tavily Extract parsing
with mocked HTTP (results, failed_results, batching at 20,
chunks cap, enrich top 8), demo mode plus visitor-key handling,
briefing quality measurement (kept and dropped counts, dated
share, source share, named-subject share, date range, categories,
cross-check against the committed Markdown headers), and the
three shown failure messages (no key, HTTP 401, no results).
The two Streamlit app import tests run only when Streamlit is
installed, because it is an optional dependency; with
streamlit==1.67.0 installed, all 74 tests pass with 0 skipped.
