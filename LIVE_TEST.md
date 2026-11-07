# LIVE TEST: Tavily Research Agent

Date of attempt: 2026-11-03
Meeting date intended for live briefings: 2026-11-03
Window intended: 2026-10-04 to 2026-11-03

## Result in one line

Live test FAILED at the verification step. No live briefing was produced.
No live company folder was created. The fixture sample in examples/
remains the only briefing output, and it must not be presented as live.

## Connector and helper built

- Connector doc: ~/workspace/custom-connectors/custom.tavily/CONNECTOR.md
- Helper: ~/workspace/custom-connectors/custom.tavily/bin/tavily_search.py
- Live runner: ~/workspace/geekroom-tavily-agent/live_briefing.py
  (reuses the existing briefing pipeline, dates, deduplication, and
  Markdown/PDF render; it does not read any key from the environment
  and does not accept a key on the command line)
- Both Python files compile: python3 -m py_compile passed.

## Verification attempts (all failed the same way)

1. Authenticated search, query "OpenAI news", topic news, basic depth,
   max_results 3, time_range month, start 2026-10-04, end 2026-11-03,
   timeout 30 seconds.
   Result: TimeoutError during the CONNECT tunnel, 0 bytes received,
   no HTTP status, no Tavily response.

2. Same authenticated search, timeout 60 seconds.
   Result: same timeout, 0 bytes received, no HTTP status.

3. Unauthenticated GET https://api.tavily.com/ and
   GET https://api.tavily.com/search, timeout 20 seconds each.
   Result: same timeout, 0 bytes received.

4. Unauthenticated POST https://api.tavily.com/search via curl,
   timeout 25 seconds.
   Result: curl exit 28, 0 bytes received, HTTP 000.

5. Verbose curl GET https://api.tavily.com/ showed: CONNECT tunnel
   established with HTTP 200, TLS 1.3 handshake completed, then no
   server response before the timeout. This rules out a simple DNS
   failure and a simple proxy connection failure for this host.

## Controls that worked

- https://example.com/ : HTTP 200 in about 1.1 seconds
- https://docs.tavily.com/ : HTTP 200 in about 1.0 seconds
- https://app.tavily.com/ : HTTP 200 in about 2.2 seconds
- https://tavily.com/ : HTTP 200 in about 2.1 seconds

Only api.tavily.com hung, in every attempt, with and without
authentication. That points to a route problem for api.tavily.com
from this environment, not to a general network outage.

## Credential-side checks (passed, but auth not proven)

- Surrogate lookup for custom.tavily succeeded and returned a
  surrogate value in the expected form.
- Placement reported by that lookup: bearer_header, which matches
  the Tavily docs and the existing client.
- Allowed host check passed for api.tavily.com.

Because no Tavily response was ever received, authentication itself
was neither proven nor disproven. No 401 or 403 was seen, so no
reconnect was requested, per the task instructions.

## Provider status check

- Tavily status page (status.tavily.com) reported fully operational
  with 100 percent uptime for the API Service over Aug to Nov 2026,
  and third-party status aggregators reported no current outage.
- This does not prove the API was reachable from this environment.
  It only rules out a known, public Tavily outage as the explanation.

## Live briefings: none

- Companies intended: OpenAI, Google, Microsoft, meeting 2026-11-03.
- Companies actually run live: none.
- Results kept per company: not applicable, no live response.
- Results dropped as too old or duplicates: not applicable.
- Live-only published_date format issues: none observed, because no
  live response was received. Offline handling for ISO dates and
  RFC/GMT dates remains covered by the 12 passing unit tests.
- Credits used: not shown, because no response was received.
  No credit cost is guessed here.

## What remains, in order

1. Retry the live run from an environment where api.tavily.com
   responds, for example the parent agent context with egress
   approval for api.tavily.com, using:
   python3 live_briefing.py --subject "OpenAI" --meeting 2026-11-03 \
     --out examples/live-openai/briefing
   Repeat for Google and Microsoft, unless coverage is empty, in
   which case pick another well-covered company and record why.
2. Record kept, dropped-old, and dropped-duplicate counts per
   company in this file, plus any live date format fixes.
3. Record a 2-minute demo video of a live run.
4. Push to a public GitHub repo, after verifying no secret is included.
5. Submit to HackCulture before Nov 15, 2026, 11:59 PM PKT, with
   Tavily Research Agent as the primary theme.

## Status kept accurate

NOT pushed to GitHub. NOT submitted to HackCulture. NOT live.
No demo video created. Nothing deleted.

---

## RETRY 2026-11-04 (scheduled 22:35 PKT, after the KezTech send window)

Meeting date used: 2026-11-04. Window: 2026-10-05 to 2026-11-04.

### Result in one line

STOPPED on the task body's step-3 condition: an authenticated call to
api.tavily.com/search returned HTTP 401 Unauthorized. No live briefing
was produced. No reconnect was requested, and the call was not retried
unchanged, per the task instructions.

### What happened, in order

1. `python3 live_briefing.py --subject "OpenAI" --meeting 2026-11-04
   --out examples/live-openai/briefing` ran. It wrote
   examples/live-openai/briefing.md and briefing.pdf, but both are
   EMPTY (0 results kept, 0 dropped old, 0 dropped duplicates, "No
   verified developments"). The run's stdout was lost when the exec
   session disappeared, so the per-category errors were not captured
   from that run. These two files are artifacts of a failed run, NOT
   live briefings, and must not be presented as live.
2. Single-category probe 1 (helper tavily_search.py, query "OpenAI
   news", max_results 3, 2026-10-05 to 2026-11-04): TimeoutError
   during the CONNECT tunnel, 0 bytes received, no HTTP status.
   Same route failure as Nov 3. Full traceback saved in
   /tmp/tavily_probe_2026-11-04.txt (ephemeral; see log entry).
3. Controls at the same time: unauthenticated GET
   https://app.tavily.com/ returned 307 in 1.34s;
   unauthenticated GET https://api.tavily.com/ returned 200 in
   0.95s (afternoon it had been 403 in 0.34s). So the api host
   itself now answers a plain GET, but that says nothing about an
   authenticated search.
4. Single-category probe 2 (same call, to test whether the route had
   recovered): urllib.error.HTTPError: HTTP Error 401: Unauthorized
   on POST https://api.tavily.com/search. Full traceback saved in
   /tmp/tavily_probe2_2026-11-04.txt. This is the step-3 stop
   condition, so work STOPPED here: Google and Microsoft were NOT
   run, and no chain step (demo video, GitHub push, pitch deck,
   HackCulture submission) was started.

### Counts per company

- OpenAI: kept 0, dropped old 0, dropped duplicates 0, because no
  live response was ever received (timeouts, then 401). Not a real
  zero-news result.
- Google: not run. Microsoft: not run.
- Live published_date format fixes: none observed, because no live
  response was received.

### What remains, in order

1. The 401 needs the user (or the account owner) to decide the next
   step: the task forbids requesting a reconnect and retrying the
   same call unchanged, so the next move is his call, not an
   automatic retry.
2. Only after an authenticated search succeeds: run live_briefing.py
   for OpenAI, Google, Microsoft with meeting 2026-11-04 (or the
   then-current date), record kept/dropped counts here.
3. Then, in order: 2-minute demo video of a live run, public GitHub
   push after verifying no .env or key is included, pitch deck from
   PITCH.md, HackCulture submission before Nov 15, 2026, 11:59 PM
   PKT, Tavily Research Agent as primary theme.

## Status kept accurate (updated 2026-11-04 ~22:40 PKT)

NOT pushed to GitHub. NOT submitted to HackCulture. NOT live.
No demo video created. Nothing deleted. No reconnect requested.

---

## RETRY 2026-11-05 (after Tavily reconnect, subagent task)

Meeting date intended: 2026-11-05. Window intended: 2026-10-06 to 2026-11-05.

### Result in one line

STOPPED at the verification step: authenticated POST to
api.tavily.com/search returned HTTP 401 Unauthorized, even after
the custom.tavily reconnect. No live briefing was produced.
No live_briefing.py run was started. No reconnect was requested,
and the same call was not retried unchanged, per the task.

### Verification attempt

- Command: `python3 ~/workspace/custom-connectors/custom.tavily/bin/tavily_search.py --query "OpenAI news" --max-results 3 --start-date 2026-10-06 --end-date 2026-11-05 --timeout 60`
- Result: `urllib.error.HTTPError: HTTP Error 401: Unauthorized`
  on POST https://api.tavily.com/search, in about 4.5 seconds.
  This is a fast auth rejection, not the Nov 3 timeout (0 bytes,
  no status, 30 and 60 second timeouts). The route now responds.
- Egress confirmation for this call in this context was approved.

### Controls run at the same time

- Unauthenticated GET https://api.tavily.com/ : HTTP 200 in 0.73s.
- Unauthenticated GET https://app.tavily.com/ : HTTP 307 in 0.68s.
- So the api host answers a plain GET, but the authenticated
  search with the reconnected custom.tavily credential was
  rejected with 401. Authentication is therefore the blocker
  now, not the route. No 403 was seen. No credit use is shown
  or guessed.

### Counts per company

- OpenAI: not run live. Google: not run live. Microsoft: not run live.
- Kept / dropped old / dropped duplicates: not applicable, no live
  response was received.
- The empty Nov 4 files in examples/live-openai/briefing.md and
  briefing.pdf (0 kept, 0 dropped, 0 duplicates) were NOT
  overwritten or deleted in this retry, because no live run was
  started. They remain failed-run artifacts, NOT live briefings,
  and must not be presented as live.
- Live published_date format fixes: none observed, because no live
  response was received.

### What remains, in order

1. The 401 after reconnect needs the parent / account owner to
   decide the next step. Do not retry the same authenticated
   call unchanged and do not request another reconnect from
   this task. Possible causes to check outside this task, not
   claimed here: the key entered on reconnect was not the
   active Tavily API key for the pakmultilinks account, the
   key was revoked or rotated, or the wrong key was copied
   from the dashboard.
2. Only after an authenticated search succeeds: run
   live_briefing.py for OpenAI, Google, Microsoft with the
   then-current meeting date, record kept/dropped counts here.
3. Then, in order: 2-minute demo video of a live run, public
   GitHub push after verifying no .env or key is included,
   pitch deck from PITCH.md, HackCulture submission before
   Nov 15, 2026, 11:59 PM PKT, Tavily Research Agent as
   primary theme.

## Status kept accurate (updated 2026-11-05, after reconnect retry)

NOT pushed to GitHub. NOT submitted to HackCulture. NOT live.
No demo video created. Nothing deleted in this retry.

---

## LIVE VIA PLAYGROUND 2026-11-05

Meeting date used: 2026-11-05. Window: 2026-10-06 to 2026-11-05.

### Result in one line

LIVE briefings produced from real Tavily data, via the Tavily API
Playground in the browser. This does NOT fix the direct API route:
authenticated calls to api.tavily.com from this environment still
return HTTP 401 (see the RETRY 2026-11-05 section above), so the
app's own live API path (live_briefing.py) is still unproven. What
is proven now is the pipeline on real Tavily results, end to end,
with honest counts and real source links.

### Searches run

- Browser task 13:46-13:50 PKT Nov 5, 2026, signed in at
  app.tavily.com as pakmultilinks@gmail.com, Researcher plan.
- Tavily API Playground, Search, topic news, search_depth basic,
  max_results 5, time_range month, Include published date checked.
- 12 searches, 4 categories per company (news, launches and product
  updates, hires and leadership, funding) for OpenAI, Google,
  Microsoft. All 12 completed, 5 results each, 60 total, none
  failed, no search returned 0.
- No new key was created, nothing was deleted, published, or
  submitted in the Playground run. No phone verification, SMS, or
  Tap Yes step was encountered.
- Transcription: examples/live-playground-2026-11-05.json, all 60
  results, titles, URLs, and snippets copied exactly as shown.
  One character change only: the em-dash character as shown by the
  Playground was replaced with a plain hyphen in 3 places (Google
  7.2 title, Google 8.1 snippet, Microsoft 10.1 title), per the
  standing project rule that the em-dash never appears in project
  output. The replacement is recorded in the JSON file's note field.
  Nothing else was expanded, completed, or guessed.
- Build: build_playground_briefings.py feeds the JSON through the
  existing tavily_agent pipeline (dates, window filter,
  deduplication, Markdown/PDF render). No call to api.tavily.com
  was made in this build.

### Honesty rules applied (recorded here, as ordered)

- Drop results with a truncated URL, because the source link cannot
  be verified. Counted as dropped_truncated_url.
- Drop Tavily knowledge-company pages (tavily.com/knowledge/company/...)
  from developments, because they are company profiles, not dated
  developments, and have no published_date. Counted as dropped_profile.
- Drop results dated outside the 30-day window, if any. Counted as
  dropped_old. Drop duplicates by normalised URL. Counted as
  dropped_duplicates.
- Keep undated results only if their URL is complete and they are not
  a profile page, flagged "date unknown". In this run every undated
  result was a profile page, so no kept development is flagged
  "date unknown".
- Every kept development carries its complete source URL and its
  published_date. Every snippet is only the truncated snippet as
  reported, or a shorter extract of it, never an invented fuller
  sentence. The summary is extractive (first sentence of the top 3
  kept snippets), so it reads as oddly as the source snippets do.
- No company ended at 0 kept, so no no-verified-developments
  briefing was needed in this run. The pipeline still produces one
  if a company ever does end at 0.

### Counts per company

- OpenAI: total 20, kept 14, dropped_old 0, dropped_duplicates 2,
  dropped_truncated_url 1, dropped_profile 3.
  Truncated URL dropped: Bloomberg, "OpenAI Shifts Value to $1.25
  Trillion as Funding Talks Finalize" (URL ends "funding-t...").
  Profiles dropped: 3 copies of the Tavily OpenAI knowledge page
  (1.1, 2.5, 4.5). Duplicates dropped: 3.4 duplicates 1.4 (Jill
  Hazelbaker) and 3.5 duplicates 1.5 (Dan Driscoll); the pipeline
  kept the first copy, under News, since the same development was
  returned by both the news and the hires searches.
- Google: total 20, kept 15, dropped_old 0, dropped_duplicates 0,
  dropped_truncated_url 5, dropped_profile 0.
  Truncated URLs dropped: Nieman Lab news AI pilot ("including-u..."),
  MPR News Pine Island data center ("pine-i..."), Patch Gemini
  workplace agent ("code-ru..."), Google Cloud Press Corner water
  infrastructure ("Infrast..."), Bloomberg Isomorphic Labs funding
  ("for-a...").
- Microsoft: total 20, kept 8, dropped_old 0, dropped_duplicates 0,
  dropped_truncated_url 10, dropped_profile 2.
  Truncated URLs dropped: Maia 300 ("cust..."), Lumen collaboration
  ("co-sell-ent..."), Surface Laptop Ultra ("announ..."), Contact
  Center Intelligence ("contact-cente..."), Copilot for Legal ("in..."),
  Register certifications ("launch..."), GeekWire Tech Moves ("ala..."),
  DCD cloud leadership ("significant-..."), GMAC MBA programs
  ("developme..."), SILive Malliotakis funding ("and-...").
  Profiles dropped: 2 copies of the Tavily Microsoft knowledge page
  (9.2, 12.2).
- TOTAL: 60 results, kept 37, dropped_old 0, dropped_duplicates 2,
  dropped_truncated_url 16, dropped_profile 5.

### Date format issues

- None. Every dated result used an RFC/GMT published_date string
  (for example "Tue, 03 Nov 2026 08:00:00 GMT"), which the existing
  parse_published_date handles. All dated results fell Oct 7 to
  Nov 5, 2026, inside the Oct 6 to Nov 5 window, so dropped_old is
  0 everywhere. No live-only date format fix was needed.
- The Nextgov URL shared by OpenAI 3.1 and Microsoft 11.2 ends with
  a bare "?" exactly as reported, with no truncation marker. It was
  treated as a complete URL and kept in both briefings. Deduplication
  is per company, so the same URL can legitimately appear once in the
  OpenAI briefing and once in the Microsoft briefing; 11.2 is an
  OpenAI story returned by the Microsoft hires search, and its
  company stays Microsoft.

### Truncation limitation

- The Playground JSON view truncates long content at about 100
  characters and truncates some very long titles and URLs. Snippets,
  titles, and URLs in the transcription are recorded exactly as
  shown, including trailing "..." where truncated. Where a result
  was a Tavily knowledge-company page, no published_date was shown.
- 16 of 60 results were dropped because their URL was truncated
  and the link could not be verified. Microsoft lost the most
  (10 of 20), which is why its briefing has only 8 developments.
- Some kept snippets are boilerplate or off-topic relative to their
  titles, exactly as Tavily returned them, and were NOT rewritten:
  Google 5.4 (ABC News, schools/AI tools) has a snippet about a
  Learjet crash in Florida; Google 8.5 snippet is "Unlock URL /
  Order Reprints / Gift this Article / Image 1: Northlake Commons
  b..."; OpenAI 1.4/3.4 and 1.5/3.5 snippets are page-chrome
  fragments. The extractive summary uses first sentences of the top
  3 kept snippets, so summaries may read oddly. That is faithful to
  the source and was not "fixed" by inventing better text.

### Files produced

- examples/live-openai/briefing.md and briefing.pdf (14 kept).
  This OVERWRITES the empty Nov 4 files in the same folder (0 kept,
  failed-run artifacts). The overwrite is recorded here, as ordered.
  No other file was deleted.
- examples/live-google/briefing.md and briefing.pdf (15 kept).
- examples/live-microsoft/briefing.md and briefing.pdf (8 kept).
- Each briefing is labelled "LIVE via Tavily Playground, Nov 5, 2026"
  with a note explaining the data source and the truncation
  limitation. Each Markdown lists every kept development with its
  URL (verified by the build script), and each PDF was verified to
  start with a %PDF- header and to contain the LIVE note, the
  truncated-URL count line, and every kept URL (Google 30 URL
  occurrences, Microsoft 16, OpenAI 28, counting the key-developments
  and sources sections).
- Pipeline change for this run, additive only: Briefing gained
  dropped_truncated_url_count, dropped_profile_count, and
  source_note fields; render_markdown and render_pdf show them when
  present. Default output is unchanged. Unit tests re-run after the
  change: 12 run, 12 passed.

### What remains, in order

1. 2-minute demo video of a live run. Do not use fixture output as
   if it were live; use the Playground live briefings or a live API
   run.
2. Public GitHub push, after verifying no .env or key is included.
   Note: the GitHub API credential expired Oct 30, 2026, so this
   may need a reconnect or a browser route.
3. Pitch deck built from PITCH.md.
4. HackCulture submission before Nov 15, 2026, 11:59 PM PKT, with
   Tavily Research Agent as the primary theme. Early submission is
   allowed and need not be final, so a first version can go in once
   the parent approves and keep improving until Nov 15.
5. Separately, the direct API 401 still needs the account owner to
   decide the next step before live_briefing.py can be proven from
   this environment. The Playground briefings do not depend on it.

## Status kept accurate (updated 2026-11-05)

Live briefings via Playground exist (OpenAI 14, Google 15,
Microsoft 8 kept, files listed above). NOT pushed to GitHub.
NOT submitted to HackCulture. No demo video yet. Nothing deleted
except the overwrite of the empty Nov 4 OpenAI briefing files
with the real OpenAI briefing, recorded above.

## Relevance-aware summary, Batch 1, 2026-11-07

### Rule

A kept development is quoted in the summary Top findings only when
the subject name appears in BOTH its title and its snippet
(case-insensitive, subject string only). A short form or a parent
company name does not count: "Alphabet" does not count as a mention
of "Google". The rule is implemented in tavily_agent/briefing.py
(mentions_subject and summary_eligible_results) and in
tavily_agent/summarizer.py (extractive_summary with a subject
argument). Discussion points and open questions still use all kept
developments, as before; only the summary Top findings changed.

Why both title and snippet: the summary quotes the first sentence
of the snippet, so a title that names the subject is not enough
when the quoted snippet does not. The Google briefing proved it:
its top finding was a snippet about a Learjet crash under a title
that did name Google.

### Excluded from the summary, per company (kept counts unchanged)

OpenAI: kept 14, excluded 4.
- "OpenAI hones public sector focus with new leadership hires -
  Yvette Kirk | LinkedIn" (snippet does not name OpenAI)
- "Introducing the Grid Protectors Program" (neither title nor
  snippet names OpenAI)
- "OpenAI Funding Round: $30B at $1.25T Value [2026]" (snippet
  does not name OpenAI)
- "OpenAI Updates ChatGPT Ads Manager with Daily Budgets Tool"
  (snippet does not name OpenAI)

Google: kept 15, excluded 11.
- "Seattle's Ai2 lands $5 million Google grant for climate modeling"
  (snippet does not name Google)
- "Google will cut off search access for students at schools that
  reject AI tools" (snippet is about a Learjet crash, does not
  name Google)
- "Google.org funds AI tools for teachers" (snippet does not name
  Google)
- "The latest AI-powered martech news and releases" (neither names
  Google)
- "How Salesforce Gets Business Leaders to Hire Ahead with Nicole
  Pruner" (title does not name Google)
- "Choosing Your First Leadership Hire: 18 Questions To Ask"
  (neither names Google)
- "GOOGLE NEWS US: Three news items about Bullying Sin Fronteras"
  (snippet does not name Google)
- "How Google's Rule of Four Can Streamline Executive Searches"
  (snippet does not name Google)
- "Enablement Leader, Google Public Sector - Google Careers"
  (snippet does not name Google)
- "Alphabet president Ruth Porat on how Google is funding AI to
  win long term" (snippet names Alphabet, not Google)
- "Google launches Gemini AI workplace agent that can write code
  and run tasks" (snippet does not name Google)

Microsoft: kept 8, excluded 4.
- "OpenAI hones public sector focus with new leadership hires -
  Nextgov/FCW" (neither title nor snippet names Microsoft)
- "Atul Sehgal - Source Asia" (neither names Microsoft)
- "AI Bond Funding Might Change The Case For Investing In
  Microsoft (MSFT)" (snippet does not name Microsoft)
- "Global health nonprofit PATH elevates its security and protects
  private data with Microsoft" (snippet does not name Microsoft)

### Verification

- Rebuilt with python3 build_playground_briefings.py. Kept counts
  unchanged: OpenAI 14, Google 15, Microsoft 8, total 37.
  Dropped counts unchanged: old 0, duplicates 2, truncated URL 16,
  profile 5. No development title, URL, date, or snippet was
  changed, and no kept development was dropped.
- New Google Top findings: CBS "Google to end search access for
  schools that block its AI tools", Citi hires Google's director
  of engineering, Google shopping updates. The Learjet crash
  snippet is no longer in the Google summary.
- New Microsoft Top findings: Edge opens 15 percent faster, $25
  billion debt raise, buyouts to 60,000 workers. The OpenAI hires
  article is no longer in the Microsoft summary.
- OpenAI Top findings unchanged (Pierre acquisition, Hazelbaker
  appointment, Nextgov hires), because its top 3 already named
  OpenAI in both title and snippet.
- Each rebuilt briefing notes its exclusion count in the Summary
  section, and the excluded developments stay in Key developments
  in full, with source links.
- Most exclusions are driven by the truncated Playground snippets,
  which often do not name the subject even when the title does.
  That is a limit of the truncated source data, not a judgement
  that the developments are irrelevant.

### PDF bold rendering check, Batch 1, 2026-11-07

- Text extraction (pdftotext) on all three live PDFs found 0
  occurrences of `**`, before and after the rebuild. The PDF
  renderer already uses plain text, not Markdown, so titles in the
  PDFs never show raw `**` markers. The `**` markers seen in the
  demo video came from the on-screen Markdown list in scene 4,
  not from the PDFs. No briefing file was changed for this check.
- Smoke check after the rebuild: all three PDFs start with
  %PDF-1.4, every kept URL in each Markdown appears in its PDF
  (OpenAI 14, Google 15, Microsoft 8), and no `**` appears in
  extracted PDF text.

## Batch 2, 2026-11-07: key hygiene, Extract, demo mode (mocked only)

No live call was made in this task. No key was used, and no key
value appears in any file. The direct API route and Tavily
Extract are still unproven live.

### Direct API key hygiene, mocked tests

- `tavily_agent/tavily_client.py`: key trimmed, empty key
  rejected before any network call, one retry only on timeout,
  never on 401, 401 raises TavilyAuthError with the fix
  (check the key in the Tavily dashboard, copy the active
  default dev key, set it as TAVILY_API_KEY, never paste it
  in chat or in code). The tvly- prefix is from a secondary
  source (Tavily MCP troubleshooting notes) and is unverified
  for this project, so a key without it only earns a warning
  and is still sent. Recorded here as unverified, not as fact.
- Mocked tests in `tests/test_live_client.py`: mocked 200
  returns one parsed result, mocked 401 raises the clear error
  and is called exactly once (no retry), mocked timeout
  retries once then succeeds, mocked timeout twice raises
  after one retry, a key with surrounding spaces is sent
  trimmed, an empty key raises before any network call, and
  `live_smoke.py` without a key exits 1 with the missing-key
  message. `live_smoke.py` was not run with a real key, so
  no live status is claimed.

### Tavily Extract, top 8 enrich only, off by default

- Verified facts, from the official docs endpoint page
  (updated 2026-09-15): POST https://api.tavily.com/extract,
  up to 20 URLs per request, query reranks chunks,
  chunks_per_source 1 to 5 (default 3, only with a query),
  basic or advanced depth, markdown or text format, timeout
  1.0 to 60.0 seconds. Check both results and failed_results
  even on HTTP 200. Extract does not return published_date.
- Cost note, from the same docs: basic 1 credit per 5
  successful extractions, advanced 2 credits per 5. Enriching
  the 37 kept URLs at basic depth, all successful, is 37 / 5
  rounded up, 8 credits. That is arithmetic from the
  documented per-5 cost, not a measured bill.
- Mocked tests in `tests/test_extract.py`: mocked 200 with
  results and failed_results, first chunk only, a URL with no
  content lands in failed, mocked 401 raises the clear error,
  chunks_per_source capped at 5, batching at 20 URLs (25 URLs
  sent as 20 plus 5), enrich touches only the top 8, enrich
  never changes a title, URL, date, or snippet.
- Default rebuild verified: `python3
  build_playground_briefings.py` with no flag made no network
  call, Markdown files byte-identical, kept counts unchanged
  (OpenAI 14, Google 15, Microsoft 8, total 37; dropped old 0,
  duplicates 2, truncated URL 16, profile 5). The regenerated
  PDFs differed only by embedded creation date and were
  restored to their committed versions, so the Batch 2 commit
  carries no briefing file changes.

### Streamlit demo mode

- Demo mode is the default in `app.py`: the three prebuilt
  live briefings, no Tavily call, no key used. Live mode uses
  a visitor key for that session only, never stored, never
  written to a file. A deployment secret is only a fallback.
- Tests in `tests/test_demo_mode.py`: demo kept counts parsed
  from the committed files (14, 15, 8), live mode disabled
  without a key, visitor key set in memory only and cleared,
  no secrets file created.
- Streamlit pinned to 1.67.0, verified as the latest release
  on pip on 2026-11-07 and installed in a test venv, where
  all 52 tests pass with 0 skipped. The app was started
  headless locally and its demo page returned HTTP 200.
  It has NOT been deployed; the deploy click needs a
  signed-in Streamlit account connected to GitHub.
