# STATUS: Tavily Research Agent MVP

Built: 2026-11-03, locally only.
Hackathon: Geek Room Global AI Hackathon, theme Tavily Research Agent.
Submission deadline: November 15, 2026, 11:59 PM PKT. Judging: November 29, 2026.
Live briefings via the Tavily Playground exist (Nov 5, 2026, see the
new section at the end of this file). Pushed to public GitHub
Nov 5, 2026: https://github.com/pakmultilinks-dot/tavily-research-agent,
branch main, commit 152cb84, 32 files, verified live. NOT
submitted yet, no demo video yet.

## What is built

- Real runnable Python app in this folder, CLI plus a standard-library web UI.
- Input: company or person name plus meeting date and time (date in the CLI and UI).
- Process: four Tavily category searches (news, launches, hires, funding),
  30-day window enforced in the request and locally, deduplication by
  normalised URL, newest-first sorting, undated results flagged.
- Output: one-page briefing in Markdown and PDF with summary, key
  developments with date plus source link each, 3 to 5 discussion points,
  and 3 to 5 open questions. Empty results give an explicit no-results
  briefing with no invented developments.
- Config: Tavily key only from TAVILY_API_KEY. No key is hardcoded and
  no key was written to any file. `.env.example` lists variable names only.
- AI use: extractive fallback by default and labelled as such. LLM
  summary only if LLM_API_KEY is set, with fallback to extractive.
- Docs: README.md, PITCH.md, this STATUS.md, `.env.example`, `requirements.txt`.

## What was tested, with real results

- Unit tests: `python3 -m unittest discover -s tests -v`
  Result: 12 tests run, 12 passed, 0 failed.
  Coverage: date parsing (ISO and RFC/GMT), window boundaries,
  future-meeting cap, old-result filtering, deduplication,
  undated handling, sorting, briefing formatting, empty results,
  and a full fixture pipeline run.
- Sample run (mock, fixtures only):
  Command: `python3 main.py --subject "Example Company" --meeting 2026-11-10 --mock --out examples/sample_briefing`
  Result: kept 4, dropped as too old 1, dropped as duplicates 1.
  Outputs: `examples/sample_briefing.md` and `examples/sample_briefing.pdf`
  (PDF header verified as PDF 1.4).
  Fixtures are invented samples in `examples/fixtures.json`, clearly
  labelled as fixtures, NOT real Tavily data and NOT real news.
- Web UI smoke test: server started on 127.0.0.1:8765, GET returned
  the form, POST with mock mode returned the sample briefing. Server
  stopped after the test. No key was used.
- Tavily API research: endpoint, auth, and parameters recorded in
  README.md with sources. `include_published_date` and per-depth credit
  costs were left unverified and are NOT sent or claimed as fact.

## Deliberate deviation, explained

The task allowed Streamlit or FastAPI for the web UI. This build uses
a Python standard-library web server instead, so the app runs with
only requests and reportlab installed. The web UI reuses exactly the
same briefing pipeline as the CLI, so it is not an HTML-only demo.
If judges prefer Streamlit, a Streamlit front end can be added later
on top of the same pipeline without changing the core logic.

## What is still missing for a live run

1. Tavily API key. The user must sign in at https://app.tavily.com/home
   in their own browser and, if they choose, redeem coupon GEEKROOM2
   for 8000 credits before November 28, 2026. No sign-in, credit claim,
   or key handling was done in this build.
2. Live test on 2 to 3 real companies. Run the CLI in live mode with
   TAVILY_API_KEY set, check that dates, sources, and the 30-day filter
   behave on real Tavily data, and fix any live-only issues (for
   example, a published_date format not seen in fixtures).
3. Optional LLM summary test, only if an LLM key is provided. Without
   it, the extractive fallback is the honest, tested path.
4. Demo video, 2 minutes, showing a live run and opening a source link.
   Do not use fixture output as if it were live in the video.
5. Public GitHub push. Create a public repo, push this folder, and
   confirm the README renders and no `.env` or key is included.
6. Final hackathon submission before November 15, 2026, 11:59 PM PKT,
   selecting Tavily Research Agent as the primary problem statement,
   with the repo link and a pitch deck built from PITCH.md.

## Exact next steps, in order

1. User: claim Tavily credits and copy the key, in their own browser.
2. User or parent agent: export TAVILY_API_KEY in a shell and run:
   `python3 main.py --subject "<real company>" --meeting <YYYY-MM-DD> --out examples/<company>`
   Repeat for 2 to 3 real companies and keep the real briefings separate
   from the fixture sample.
3. Record a 2-minute demo of a live run.
4. Push to a public GitHub repo, verify no secret is included.
5. Build the pitch deck from PITCH.md and submit before the deadline.

## Blockers for live testing

- No Tavily API key was available to this build, by design. Live mode
  cannot be tested until a key is provided via environment variable.
- No LLM key was available, so the LLM summary path is untested live.
  The extractive path is tested and is the default.
- Nothing was deleted, pushed, published, or submitted in this build.

## Live test attempt, 2026-11-03 (connector route, NOT completed)

- Connector doc created: ~/workspace/custom-connectors/custom.tavily/CONNECTOR.md
- Helper created and compiled: ~/workspace/custom-connectors/custom.tavily/bin/tavily_search.py
- Live runner created and compiled: live_briefing.py in this folder.
  It uses the connector surrogate route only, not TAVILY_API_KEY.
- Verification FAILED: authenticated and unauthenticated calls to
  api.tavily.com timed out from this environment after TLS, with
  0 bytes received and no HTTP status, at 30, 60, 25, and 20 second
  timeouts. Controls (example.com, docs.tavily.com, app.tavily.com,
  tavily.com) responded in about 1 to 2 seconds. Surrogate lookup
  for custom.tavily succeeded with bearer_header placement, so the
  failure is recorded as a route failure, not as a 401 or 403.
  No reconnect was requested.
- Live briefings produced: none. No live company folders exist.
  Full record: LIVE_TEST.md in this folder.
- This project is still NOT live, NOT pushed to GitHub, and
  NOT submitted. Nothing was deleted.
- Next step for the parent: retry live_briefing.py from an
  environment where api.tavily.com responds, then update
  LIVE_TEST.md with real kept and dropped counts before any
  demo video, public push, or submission.

## Live test retry, 2026-11-05 (after Tavily reconnect, NOT completed)

- Reconnect of custom.tavily had completed before this retry.
  No key was asked for again, no key value was written or
  reported anywhere in this retry.
- Verification: one authenticated search via
  tavily_search.py, query "OpenAI news", max_results 3,
  2026-10-06 to 2026-11-05, timeout 60.
  Result: HTTP 401 Unauthorized on POST
  https://api.tavily.com/search, in about 4.5 seconds.
  This is a fast auth rejection, not the Nov 3 timeout.
- Controls at the same time: unauthenticated GET
  api.tavily.com returned 200 in 0.73s, app.tavily.com
  returned 307 in 0.68s. The api host answers, but the
  authenticated search with the reconnected credential
  was rejected.
- Per the task, work STOPPED immediately: no
  live_briefing.py run was started, Google and Microsoft
  were not run, the same call was not retried unchanged,
  and no further reconnect was requested.
- Live briefings produced: none. The empty Nov 4 OpenAI
  files in examples/live-openai/ were left untouched.
  The fixture sample in examples/ remains the only
  briefing output and must not be presented as live.
- Full record: LIVE_TEST.md, new RETRY 2026-11-05 section.
- This project is still NOT live, NOT pushed to GitHub,
  and NOT submitted. Nothing was deleted in this retry.
- Next step for the parent / account owner: decide how to
  resolve the 401 after reconnect (for example, verify in
  the Tavily dashboard that the key entered is the active
  key for the correct account). Do not retry the same
  authenticated call unchanged until that is resolved.

## Live briefings via Playground, 2026-11-05

- Real Tavily data, gathered in the Tavily API Playground in the
  browser (13:46-13:50 PKT Nov 5, 2026, signed in as
  pakmultilinks@gmail.com, Researcher plan), transcribed exactly as
  shown into examples/live-playground-2026-11-05.json (60 results),
  then built through the existing pipeline by
  build_playground_briefings.py. No call to api.tavily.com was made
  in this build, and no key value was written or reported anywhere.
- OpenAI: 14 kept (examples/live-openai/briefing.md and .pdf).
  Google: 15 kept (examples/live-google/briefing.md and .pdf).
  Microsoft: 8 kept (examples/live-microsoft/briefing.md and .pdf).
  Total kept 37 of 60. Dropped: 16 truncated URL, 5 profile pages,
  2 duplicates, 0 too old. Each briefing is labelled LIVE via
  Tavily Playground with a note on the source and the truncation
  limitation. Markdown and PDF smoke-checked (PDF header, LIVE
  note, count lines, every kept URL present).
- The empty Nov 4 OpenAI files were overwritten with the real
  OpenAI briefing, recorded in LIVE_TEST.md. No other file deleted.
- Unit tests re-run after the small additive pipeline change
  (Briefing gained truncated-URL count, profile count, and source
  note): 12 run, 12 passed.
- Honest limit: this does NOT prove the app's direct API path.
  Authenticated calls to api.tavily.com from this environment
  still return HTTP 401, so live_briefing.py is still unproven.
  The Playground briefings prove the pipeline on real Tavily
  results, not the API client route. The 401 still needs the
  account owner to decide the next step.
- Full record: LIVE_TEST.md, "LIVE VIA PLAYGROUND 2026-11-05".

## Repo and pitch deck ready, 2026-11-05 (PUSHED same day, NOT submitted)

- Secret scan, Nov 5: no real key, no .env file, no credential,
  no password, no private key in the folder. Only placeholders
  (`TAVILY_API_KEY=` empty in .env.example, `<redacted>` in docs)
  and code references to the env var name. The only personal
  identifier present is the Tavily account email in the live
  briefing notes, STATUS.md, LIVE_TEST.md, and the source JSON
  note; it was kept because it is part of the verified live
  artefacts, and the parent can decide to scrub it before push.
- Em-dash check: 0 in README.md, PITCH.md, STATUS.md, and the
  whole folder (the 3 em-dashes from the Playground transcription
  were already replaced with hyphens in the live JSON).
- .gitignore now covers .env, __pycache__/, *.pyc, venv/, .venv/,
  env/, *.egg-info/, dist/, build/, .DS_Store. No git repo exists
  in this folder yet; the parent must create the remote repo first.
- README.md updated with the live Playground results (counts table,
  file locations, reproduce command, honest API limit) and the
  Limitations section now states the direct API route is unproven.
- PITCH.md updated to the live state (demo flow uses the live
  briefings, working prototype lists them, remaining work is demo
  video, push, submission, and the unproven API route).
- Pitch deck built from PITCH.md, 10 slides, PDF and PPTX:
  pitch-deck.pdf (10 pages, PDF 1.4, verified with pdfinfo) and
  pitch-deck.pptx (10 slides, verified). Slides: title, problem,
  solution, demo flow, architecture, live proof, live findings,
  AI use, impact, limitations plus next steps plus why it wins.
  No em-dash, no invented metrics, no fake logos.
- Unit tests re-run: 12 run, 12 passed.
- PUSHED same day, Nov 5, 2026: public repo
  https://github.com/pakmultilinks-dot/tavily-research-agent,
  branch main, commit 152cb84, 32 files, verified with
  gh repo view and git ls-remote HEAD. The gh CLI is logged in
  as pakmultilinks-dot, so no reconnect or browser route was
  needed. Still NOT submitted to HackCulture, no demo video yet.
- Next steps, in order: 2-minute demo video (use the live
  Playground briefings, never fixture output as if live),
  HackCulture submission before Nov 15, 2026, 11:59 PM PKT.

## Demo video, 2026-11-05

- File: demo-video.mp4, 4.2 MB, 117.3 seconds, 1920x1080,
  H.264 video plus AAC audio, faststart. Verified with ffprobe:
  one video stream, one audio stream, duration 117.30s.
- Method: REAL screen recording, not a slideshow. A tkinter demo
  window was driven live under Xvfb at 1920x1080 and recorded
  with ffmpeg x11grab at 30 fps, while the real CLI run
  (build_playground_briefings.py) streamed its real output, the
  real unit tests ran, and page 1 of the three real briefing PDFs
  scrolled on screen. Voiceover was synthesized with the tts tool
  (Helio voice) from a 279-word script in demo_assets/narration.txt,
  7 segments, 117.3 seconds total, with 0.7 second gaps between
  segments. Silence check: no silent stretch longer than 2 seconds.
- Narration summary: the meeting problem, how the agent works
  (30-day window, news, launches, hires, funding), the live run
  rebuilding briefings from 60 real Tavily results, the kept counts
  (OpenAI 14, Google 15, Microsoft 8) with named examples, the
  architecture and 12 passing tests, the honest limits (short
  Playground snippets, direct API route still 401), and the public
  GitHub repo plus close.
- Live briefings only: the fixture sample is never shown as live.
  The Playground source is stated in the narration and visible on
  screen in the briefing PDF pages.
- Frame check: 9 frames sampled across all 7 scenes and viewed.
  Titles match the narration playing at that time, no text overlaps,
  no em-dash on screen. Two small imperfections, both visible in
  the frames: the briefing list in scene 4 shows raw markdown
  ** markers around development titles (the rendered PDF pages
  later in the same scene show them properly), and a small mouse
  I-beam cursor sits near the centre of the dark scenes.
- One recording attempt failed first (a Tkinter callback race
  cut a PDF scroll short); the race was fixed by driving scene
  animations with time.sleep plus update_idletasks instead of
  root.update, and the final recording ran clean with all 7 scenes
  on schedule and no errors.
- Reproduce: demo_assets/demo_player.py, timeline and narration
  are in demo_assets/. The live briefing PDFs were restored to
  their committed versions after the on-screen rebuild, so the
  repo working tree shows only demo-video.mp4 and demo_assets/
  as untracked.
- NOT pushed to GitHub yet in this task. The parent will push the
  video after verifying it, then it can be added to the saved
  HackCulture submission via Edit before the final submit.
