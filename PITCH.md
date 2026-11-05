# Pitch deck outline: Tavily Research Agent

Use this outline to build the slide deck. Keep each slide to one
idea. Do not add claims that are not in the README or STATUS.md.

## 1. Problem

Meetings start cold. Before an important meeting, you need to know
what a company or person did in the last 30 days: news, launches,
hires, funding. Manual search is slow, and plain AI answers mix old
and new information without sources you can check.

## 2. Solution

Tavily Research Agent. Type a name and a meeting date, get a
one-page briefing in seconds: summary, key developments with dates
and source links, discussion points, and open questions.

Demo flow for judges:

1. Open the CLI or web UI.
2. Enter a real company name and a meeting date.
3. Show the four Tavily searches running (news, launches, hires, funding).
4. Show the briefing: newest first, duplicates removed, old results dropped.
5. Open one source link to prove it is real.
6. Show the Markdown and PDF exports, same content.

For the current build, step 2 to 5 can be shown with the live
Playground briefings: OpenAI (14 kept), Google (15 kept), Microsoft
(8 kept), built Nov 5, 2026 from 60 real Tavily Playground results.
Do not present the mock fixtures as live results. The direct API
route is still unproven (401), see STATUS.md.

## 3. Technical architecture

Input (CLI or stdlib web UI)
-> Tavily Search API: POST https://api.tavily.com/search, Bearer auth,
topic=news, time_range=month, start_date and end_date for the 30-day window
-> Date parsing (ISO and RFC/GMT), window filter, URL deduplication, sorting
-> Extractive summary, optional LLM summary only if LLM_API_KEY is set
-> Markdown and PDF output

Key design choices:

- 30-day window is enforced twice: once in the Tavily request
  (time_range plus start_date and end_date) and once locally, so an
  old result cannot slip through.
- Undated results are flagged, never given an invented date.
- Empty results produce an explicit "no results" briefing, not a
  made-up briefing.
- No key is hardcoded. Tavily key comes only from TAVILY_API_KEY.

## 4. Working prototype

What exists now, locally, tested:

- CLI that builds a briefing from fixtures end to end
- Web UI that builds the same briefing from fixtures
- 12 offline unit tests, all passing
- Sample briefing in Markdown and PDF in examples/
- Live briefings from real Tavily Playground data, Nov 5, 2026:
  OpenAI 14 kept, Google 15 kept, Microsoft 8 kept, 37 of 60
  results, in examples/live-openai/, examples/live-google/, and
  examples/live-microsoft/, Markdown and PDF each

What is NOT done yet:

- Demo video
- Public GitHub push and final hackathon submission
- A proven direct API run (live_briefing.py still returns 401
  from this environment; the Playground briefings prove the
  pipeline on real Tavily data, not the API client route)

See STATUS.md for the exact remaining steps.

## 5. Use of AI

Tavily Search for real-time research and ranking. Extractive
summarisation by default, so the summary cannot invent facts.
Optional LLM summarisation only on supplied snippets, with fallback
to extractive on any failure, and the mode labelled in the briefing.

## 6. Impact and scalability

- Saves preparation time before every sales, hiring, partnership,
  or investor meeting.
- Works for any company or person with public web coverage.
- Scales by adding categories, languages, or export formats,
  without changing the core filter and sourcing rules.
- Cost is bounded: 4 searches per briefing, basic depth by default,
  no raw content fetched.

## 7. What makes this win

Finished, working, and honest. Judges can run it, see real sources
in the live briefings, and see the 30-day rule enforced in code and
in tests. The project shows its live numbers and its one honest
limit (the direct API route is unproven) instead of hiding them.
