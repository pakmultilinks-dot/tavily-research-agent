# Improvement Plan, Batch 2

Project: Tavily Research Agent
Repo: https://github.com/pakmultilinks-dot/tavily-research-agent
Status on 2026-11-07: HackCulture submission is locked Under Review and cannot be edited. The GitHub repo is free to change, and judges clicking the repo link will see the latest repo version. Judging is Nov 29, 2026.
Batch 1, done and pushed, commit 9c036e7: Streamlit UI app.py, relevance-aware summary, rebuilt pitch deck, 23 tests, 21 passed plus 2 skipped without Streamlit. CI workflow file exists locally at .github/workflows/ci.yml but is not on GitHub yet, because the command line token lacks workflow scope, so it must be added via the GitHub web UI.
Live briefings, Nov 5, 2026, via Tavily Playground: 60 results, kept 37 (OpenAI 14, Google 15, Microsoft 8). Snippets are truncated at about 100 characters. Direct API route still returns 401 with the stored credential, live_briefing.py is still unproven.
Judging criteria: innovation, technical execution, problem and potential impact, use of AI, user experience, scalability and potential.

## 1. Tavily Extract API

Source, verified by direct fetch on 2026-11-07:
https://docs.tavily.com/documentation/api-reference/endpoint/extract
Page updated: 2026-09-15.

### Verified facts

- Endpoint: POST https://api.tavily.com/extract
- Auth: Authorization Bearer header with the Tavily API key
- Body: application/json
- Extract content from one URL or batch up to 20 URLs in one request. Successful URLs appear in results. Per-URL failures appear in failed_results. Check both arrays even when the response is HTTP 200. Request options apply to every URL in the batch. Output order is not guaranteed.
- Parameters:
  - urls, required, string or list of URLs
  - query, optional string, user intent for reranking extracted content chunks. When provided, chunks are reranked based on relevance to this query.
  - chunks_per_source, integer, default 3, range 1 to 5, only when query is provided. Chunks are short content snippets, about 800 characters each, pulled directly from the source. They appear in the raw_content field as chunk 1, chunk 2, chunk 3. If a page splits into no more chunks than chunks_per_source, its full content is returned.
  - extract_depth, basic (default) or advanced. Advanced retrieves more data, including tables and embedded content, with higher success but may increase latency. Basic costs 1 credit per 5 successful URL extractions. Advanced costs 2 credits per 5 successful URL extractions.
  - include_images, boolean, default false
  - include_favicon, boolean, default false
  - format, markdown (default) or text. Text may increase latency.
  - timeout, number, 1.0 to 60.0 seconds. Default timeouts: 10 seconds for basic, 30 seconds for advanced.
  - include_usage, boolean, default false. The usage value may be 0 if the total successful URL extractions has not yet reached 5 calls.
- Response: results (list of extracted content), failed_results (list of URLs that could not be processed), response_time (seconds), usage (credit usage details), request_id (unique identifier for support).
- Python SDK usage, from the same docs family: client.extract(urls=[...], extract_depth="advanced", format="markdown"). Verified only from the Tavily Python SDK docs summary, not from a live call.

### Can it fix the truncated snippet problem?

Yes, partly, and this is the clearest Batch 2 win for briefing quality.

- The Nov 5 problem is not in the search results themselves. It is in the Playground JSON view, which truncates snippets at about 100 characters. Extract returns the real page content, or with a query, up to 5 chunks of about 800 characters each per source, about 4000 characters per source at most.
- With Extract, the summary can use the first real paragraph from each kept source, instead of a truncated snippet. Discussion points and open questions can quote real content, with the same source URL and the same published date from the search result.
- Cost is low. For the 37 kept URLs, basic depth, all successful: 37 divided by 5, rounded up, is 8 credits. The account balance after the Nov 3 coupon was 9000 credits, with 2 used in the first Playground test, so 8 credits is small. Advanced depth would be 16 credits for the same 37 URLs. These numbers are arithmetic from the verified per-5 cost, not a measured bill.
- Limits, all verified or directly implied by the docs:
  - Extract does not return published_date. Keep the date from the search result. Do not overwrite it.
  - Paywalled and bot-blocked pages will fail. They go in failed_results. The briefing must keep the search snippet as fallback for those URLs, and must say so.
  - Extract is a second API call with the same Bearer key as Search. If the stored credential is wrong, Extract will return 401 just like Search. Extract does not fix the 401 problem. It only fixes the snippet length problem, after the key problem is fixed.
  - Latency: up to 10 seconds basic, 30 seconds advanced, per batch. Batch the 37 URLs in groups of 20, two calls, not 37 calls.

### Unverified

- Exact field names inside each results entry beyond url, raw_content, images, and favicon. The docs page collapsed the child attributes in the text fetch, so field names other than those four are unverified here.
- Whether advanced depth bypasses any specific paywall. The docs say higher success, not guaranteed success.
- Exact credit counting when include_usage is on and fewer than 5 URLs succeed. The docs note the value may be 0 in that case.

## 2. Bifrost integration, Option 3

Source, verified by search results on 2026-11-07, from Maxim guides:
https://www.getmaxim.ai/articles/self-hosted-ai-gateway-for-cursor-with-claude-or-ollama/
https://www.getmaxim.ai/articles/use-claude-code-with-openai-models-via-an-ai-gateway/
https://www.getmaxim.ai/articles/how-to-choose-an-ai-gateway-in-2026-10-critical-factors-for-your-ai-stack/
Bifrost repo, from earlier project notes: https://github.com/maximhq/bifrost
Docs home, attempted fetch on 2026-11-07: https://docs.getmaxim.ai/bifrost returned 404, so the exact docs path is unverified. Do not link to it as a verified source until the correct path is confirmed.

Organiser Option 3, from the Nov 4 organiser notification: one product combining one Tavily problem and one Bifrost problem is eligible for both prize pools, without two separate projects.

### Verified facts from the Maxim guides

- Bifrost is an open source gateway by Maxim, built in Go. It exposes a single OpenAI-compatible HTTP API and routes requests to 25 or more providers and 10000 or more models. Model names use provider/model-name format, for example openai/gpt-5, anthropic/claude-sonnet-4-5-20250929, gemini/gemini-2.5-pro, ollama/llama3.3:70b.
- It runs as a self-hosted gateway, by Docker (docker run -p 8080:8080 maximhq/bifrost) or by NPX (npx -y @maximhq/bifrost). Dashboard at http://localhost:8080.
- It translates requests between formats, for example Anthropic Messages API to OpenAI Chat Completions, and back.
- Fallback chains are defined in configuration, for example {"model": "gpt-4o", "fallbacks": ["azure/gpt-4o", "bedrock/anthropic.claude-3-5-sonnet"]}. If the first provider fails, Bifrost routes to the next. Virtual keys give budgets, rate limits, and model allowlists. Observability and request logs are built in.
- Overhead claim, vendor source only, not independently verified: 11 microseconds per request at 5000 requests per second.

### What would fit this project

- The smallest honest extension point is not forking Bifrost. It is pointing the existing optional summary call at a Bifrost endpoint instead of a direct provider endpoint.
- Current code: the summariser uses an LLM summary only if LLM_API_KEY is set, otherwise it uses the extractive fallback and labels the mode. The Bifrost change would add BIFROST_BASE_URL (default http://localhost:8080/v1) and BIFROST_MODEL (for example openai/gpt-5, with a fallback list) as optional environment variables, and send the same OpenAI-compatible chat completions request through Bifrost. If Bifrost is not running or returns an error, the code falls back to the extractive summary, exactly as it does today when no LLM key is set.
- Code size estimate: about 80 to 150 lines in tavily_agent/summarizer.py, plus config in .env.example, docs in README.md, and tests with mocked HTTP responses. No Bifrost server code would live in this repo. Bifrost would run separately, by Docker or NPX, with its own provider key configured in its dashboard.
- What it would prove: provider routing, automatic fallback, and a single gateway for the summary step. What it would not prove: a Bifrost extension, a Bifrost plugin, or an upstream pull request.

### Risks to the locked Tavily-only submission

- High risk if claimed wrongly. The HackCulture submission is locked Under Review, Theme AI Agents and Intelligent Systems, Problem Statement Tavily Research Agent, Bifrost checkboxes unchecked. Adding Bifrost code to the repo does not change the locked form. Judges clicking the repo link will see Bifrost code, but the form still says Tavily only. Claiming both prize pools in the README after the lock would contradict the submitted form and look inconsistent. Do not claim both pools in the repo until the form rules are checked.
- The earlier Bifrost problem statement, from project notes, required using supported extension points, working with a standard Bifrost installation, setup, docs, and tests, suitable as an upstream pull request. Simply pointing an HTTP client at Bifrost is gateway use, not an extension. Whether that satisfies the Bifrost problem statement is unverified. The actual Bifrost problem statement text on HackCulture was not fetched in this research task, because this task does not use a live browser. That check is open for the parent.
- Bifrost needs a provider key (OpenAI, Anthropic, Gemini, or a local Ollama model) to do anything. This project has no such key on file. Without it, the Bifrost path cannot be tested live, only mocked.
- Judges cannot reproduce the Bifrost path from the repo alone. They would need Docker, a Bifrost run, and a provider key. That weakens reproducibility, which is a judging factor for technical execution.
- Recommendation: keep Bifrost as an optional, disabled-by-default path, with the extractive fallback as the default. Do not rename the theme. Do not claim both pools. Rank it last in Batch 2, after the three items in section 5.

## 3. Streamlit Cloud deployment

Source, verified by direct fetch on 2026-11-07:
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

### Verified facts from the official docs

- Streamlit Community Cloud deploys apps in one click, most apps deploy in a few minutes. Go to the workspace, click Create app, fill in repo, branch, and entry file, click Deploy.
- Every git push to the linked branch redeploys automatically, per third-party guides citing Streamlit docs. That redeploy behaviour was not verified on the official overview page fetched, which only describes the Create app flow.
- Secrets: storing unencrypted secrets in a git repository is bad practice. Community Cloud lets the owner save secrets in the app settings. Locally, code reads secrets from .streamlit/secrets.toml with st.secrets. That file must never be committed. When deploying, paste the contents of secrets.toml into the Advanced settings dialog, or update them later in app settings.
- The app.py file already exists in this repo (Batch 1). requirements.txt already lists streamlit>=1.30. The official guidance, from third-party guides citing Streamlit docs, is to pin the Streamlit version, because an unpinned app can be upgraded without notice.

### Free tier limits, secondary sources only

- Third-party guides citing Streamlit docs, dated Feb 2024 in those guides, list: memory 690 MB minimum to 2.7 GB maximum per app, CPU 0.078 to 2 cores, storage up to 50 GB, sleep after 12 hours without traffic, unlimited public apps, one private app at a time, no custom domain, URL on streamlit.app.
- These limits are unverified on the official pages fetched in this task. Treat them as secondary and subject to change. The sleep behaviour is consistent across several independent guides, so it is the most reliable of the secondary claims.
- No credit card is required for Community Cloud, per third-party guides. That claim is also secondary.

### Secrets handling for TAVILY_API_KEY

- Put TAVILY_API_KEY in Community Cloud secrets, read it with st.secrets, with an environment variable fallback for local runs. Never commit .streamlit/secrets.toml. Add it to .gitignore.
- Risk: if the deployed app calls Tavily live with the owner's key, any visitor can spend the owner's credits. Search basic is 1 credit per call in secondary sources, not verified on the official search page fetched. With 9000 credits, a public live app could still be drained by repeated use.
- Mitigation, recommended: deploy in read-only demo mode by default. The app shows the three prebuilt live briefings (OpenAI, Google, Microsoft) with no Tavily call. Live mode is available only when a visitor enters their own key, which is used for that session only and never stored. That keeps the public link always working, even if the app sleeps, and spends zero owner credits.

### Would a live deployed link help judges?

- Yes, strongly. Winning-project guides agree on this point: judges want a live demo they can see in 30 seconds, with no setup, no clone, no key. A streamlit.app link in the README gives them that. The locked HackCulture form cannot take a new link, but judges clicking the repo link will see the README and the live link there.
- Feasibility: yes, feasible. Effort is small to medium: pin the Streamlit version, add demo mode to app.py, add .streamlit/config.toml, test locally, then deploy from the Streamlit workspace connected to GitHub. The deploy click itself needs a signed-in Streamlit account connected to GitHub, which is a parent step, not a code step. The app will sleep after 12 hours without traffic, so a judge visiting later will see a wake-up screen first. That is a known limit, not a failure.

## 4. Winning AI agent hackathon projects

Sources, public search results only, fetched 2026-11-07. No specific winning team, score, or project name is claimed here, because none was verified in this research.

- https://www.tinyfish.ai/blog/how-to-win-a-hackathon-with-ai
- https://www.masaischool.com/blog/how-to-win-an-ai-hackathon-in-2026-full-guide/
- https://hackathon-vault-ten.vercel.app/
- https://www.institutepm.com/knowledge-hub/ai-hackathon-playbook
- https://hack4hack.com/hackathons/agentx-hackathon-2026-hooc

### What the guides agree on

- Judges want four things: a real problem, live data, a 30-second demo, and a clear explanation of how it works.
- Live web data wins. The demo moment that separates winners is when something real happens on the real web, right now, not on a fake demo file. A working demo beats a beautiful slide deck every time.
- Typical rubric weights, from the guides, not from this hackathon: innovation about 20 percent, technical implementation about 25 percent, problem-solving impact about 25 percent, presentation the rest. AgentX, a separate 2026 agent hackathon, lists problem fit and real-world impact 25 percent, agent design 25 percent, working demo and reliability 20 percent, innovation 15 percent, presentation 15 percent. This hackathon lists innovation, technical execution, problem and potential impact, use of AI, user experience, scalability and potential, with no published weights in the project notes.
- A working slice end to end, shipped early, beats a stronger build that is not demo-able. Judges see 30 to 100 demos in a day. The first 30 seconds of the pitch decide attention. A judge spends about 3 to 5 minutes per demo.
- Failure modes the guides name: a problem statement that is too broad, a demo that crashes live, a pitch that is a feature list instead of a story, and no measurable outcome.

### What this project does not yet show

- A live end-to-end run on demand with a fresh subject, not only the Nov 5 prebuilt briefings. The prebuilt briefings prove the pipeline, but a judge cannot type a new company name today and see a fresh briefing without a key and a local run.
- A public live URL. Judges must clone the repo and run it locally. The Streamlit app exists, but it is not deployed.
- A 30-second first screen. The demo video is 117 seconds, and the GitHub blob link for it does not play inline. GitHub says it cannot show files that big right now. Judges must click View raw or Download to watch it.
- Evaluation proof. There is no measured quality number for the briefings, for example relevance, freshness, or source coverage, beyond kept and dropped counts. There is no user test with a real meeting user.
- A real user story with a measurable outcome, for example time saved per meeting prep, or a before and after comparison with manual prep.
- Failure handling shown in the demo, for example what the app does when Tavily returns zero results, when a source is paywalled, or when the API returns an error. The code handles these cases, but the demo does not show them.
- A scalability story beyond three companies, for example cost per briefing in credits, time per briefing, and what happens with ten companies at once.

## 5. Ranked Batch 2 list

Ranking is by judging weight first, then by effort. Effort is in builder hours, not calendar days.

### Top 3, in order

#### 1. Fix the direct API 401 proof, with key hygiene checks

- Judging weight: highest. Technical execution and use of AI both depend on the direct Tavily API working, not only on Playground data.
- Effort: small to medium, about 1 to 2 hours of code, plus a key verification step that needs the parent.
- Files to change: tavily_agent/tavily_client.py, live_briefing.py, tests/test_briefing.py, plus a new tests/test_live_client.py with mocked HTTP, LIVE_TEST.md, README.md.
- Work: add a clear key format check (keys start with tvly-, per Tavily MCP troubleshooting, secondary source, unverified for this project), strip leading and trailing spaces, return a clear error message on 401 that names the fix (check the key in the dashboard, create a fresh key if needed, never paste the key in chat or in code), and log the HTTP status without logging the key. Add a single retry only on timeout, never on 401. Add a live smoke script that calls POST https://api.tavily.com/search with max_results 1 and reports status only.
- Tests to add: mocked 200 with one result, mocked 401 with a clear error, mocked timeout with one retry, key with surrounding spaces trimmed, empty key rejected before any network call.
- Honest risk: this cannot be proven in the sandbox without a fresh working key. If the key on file is wrong, Extract and live mode both stay unproven. Do not guess a key. Do not put a key in the repo. If the parent cannot verify a fresh key, record the 401 as still open and keep the Playground briefings as the live proof.

#### 2. Tavily Extract for full content, top 8 enrich only

- Judging weight: high. Technical execution, use of AI, and user experience all improve when summaries use real first paragraphs instead of truncated snippets.
- Effort: medium, about 150 to 250 lines of new code, plus tests and docs.
- Files to change: new tavily_agent/extract.py, tavily_agent/briefing.py (attach extracted text to each kept development), build_playground_briefings.py (optional enrich step, off by default), tests/test_extract.py (new, mocked HTTP), README.md, LIVE_TEST.md, STATUS.md.
- Work: call POST https://api.tavily.com/extract with urls in batches of 20, query set to the subject plus category, chunks_per_source 3, extract_depth basic, format markdown. Attach the first extracted chunk to each kept development as full_content, keep the original search snippet, keep the published date from Search, keep the source URL unchanged. If Extract fails for a URL, keep the snippet and record it in failed_results. Rebuild the three live briefings only after the key problem in item 1 is fixed, or with mocked Extract responses for the tests. Cost for the 37 kept URLs, basic depth, all successful: 8 credits.
- Tests to add: mocked Extract 200 with results and failed_results, mocked Extract 401 falls back to snippet, chunks_per_source capped at 5, batching at 20 URLs, date from Search is never overwritten by Extract.
- Honest risk: same 401 risk as item 1, plus paywall failures, plus latency up to 10 seconds per batch. Keep the snippet fallback. Do not present extracted content as a new development. Do not change any kept count.

#### 3. Live Streamlit deployment in read-only demo mode

- Judging weight: high. User experience and presentation improve most when a judge can click and see the app in 30 seconds.
- Effort: small to medium, about 1 to 2 hours of code, plus a deploy click by the parent.
- Files to change: app.py (add demo mode showing the three prebuilt live briefings, plus a visitor key input for live mode), requirements.txt (pin streamlit to a specific version), new .streamlit/config.toml, README.md (live link placeholder, deploy steps, sleep note), STATUS.md, tests for the demo mode data path.
- Work: default mode is demo, no Tavily call, no owner key used. Live mode uses a visitor key for that session only, never stored, never logged. Add a clear note in the app: demo data is from Nov 5, 2026, live mode needs a Tavily key. Add a wake-up note for the 12 hour sleep limit.
- Tests to add: demo mode loads all three prebuilt briefings, live mode is disabled without a key, a visitor key is never written to disk.
- Honest risk: the app sleeps after 12 hours without traffic, so a judge may see a wake-up screen. The live link cannot be added to the locked HackCulture form, only to the README. If the deploy uses the owner's key in secrets, visitors could spend owner credits, so demo mode must stay the default.

### Next, in order

#### 4. More live companies, 2 to 3 new, via the Playground route

- Judging weight: medium. More proof, more impact, but diminishing returns after the first three companies.
- Effort: medium. Needs a browser run by the parent, 12 searches per 3 companies, transcription, rebuild, and a new demo video cut if the new briefings are shown.
- Files: examples/live-playground-2026-11-07.json (new, dated), examples/live-<company>/briefing.md and briefing.pdf, LIVE_TEST.md, README.md, STATUS.md.
- Risk: same truncated snippet problem as Nov 5, same 401 problem for the direct route. Do this after item 2, so the new briefings can use Extract.

#### 5. Demo video v2, 90 seconds

- Judging weight: medium. Presentation improves, but the GitHub blob link still will not play inline.
- Effort: medium to high. Re-record with the Batch 1 fixes: no raw markdown markers in scene 4, no mouse cursor in dark scenes, add a shot of the GitHub repo page, add a short music bed under the narration, cut to 90 seconds.
- Files: demo-video.mp4 (replace in repo), demo_assets/ (rebuild), STATUS.md, README.md.
- Risk: replacing demo-video.mp4 in the repo updates what judges see when they click View raw or Download, even though the HackCulture form is locked. It does not fix the inline preview problem. A hosted video link would fix that, but the form is locked and cannot take a new link.

#### 6. Bifrost routing, optional and disabled by default

- Judging weight: medium to high if it worked, low as ranked here because of risk.
- Effort: medium, about 80 to 150 lines, plus docs and mocked tests.
- Files: tavily_agent/summarizer.py, .env.example, README.md, tests/test_summarizer_bifrost.py (new, mocked HTTP), STATUS.md.
- Work: add BIFROST_BASE_URL and BIFROST_MODEL as optional environment variables, send the OpenAI-compatible chat completions request through Bifrost, fall back to extractive summary on any error. Document the Docker and NPX start commands. Do not change the theme. Do not claim both prize pools.
- Honest risk: highest in this list. The submission is locked as Tavily only, the Bifrost problem statement text is unverified, a provider key is needed and is not on file, and judges cannot reproduce the path without Docker and a key. Do this only after items 1 to 3 are done, and only after the parent checks the Bifrost problem statement text on HackCulture.

#### 7. CI workflow, add via GitHub web UI

- Judging weight: low to medium. Technical execution signal, cheap to do.
- Effort: 5 minutes, parent step, no code.
- Files: .github/workflows/ci.yml, already ready locally, not on GitHub yet because the command line token lacks workflow scope.
- Work: add the file via the GitHub web UI, confirm the first CI run passes on main.

## 6. What not to do in Batch 2

- Do not change the HackCulture submission. It is locked Under Review. Do not create a second project.
- Do not claim both prize pools in the README. The form says Tavily only.
- Do not put any key, credential, or secrets file in the repo. Do not paste a key in chat or in code.
- Do not present fixture data as live data. Do not present mocked test data as live proof.
- Do not delete any file. Do not overwrite the Nov 5 live JSON source file.
- Do not change the live kept counts (OpenAI 14, Google 15, Microsoft 8) without a dated record in LIVE_TEST.md explaining why.

## Sources

- Tavily Extract, official docs: https://docs.tavily.com/documentation/api-reference/endpoint/extract
- Tavily Search, official docs, from project notes: https://docs.tavily.com/documentation/api-reference/endpoint/search
- Bifrost, Maxim guides: https://www.getmaxim.ai/articles/self-hosted-ai-gateway-for-cursor-with-claude-or-ollama/ , https://www.getmaxim.ai/articles/use-claude-code-with-openai-models-via-an-ai-gateway/ , https://www.getmaxim.ai/articles/how-to-choose-an-ai-gateway-in-2026-10-critical-factors-for-your-ai-stack/
- Bifrost repo: https://github.com/maximhq/bifrost
- Bifrost docs home, attempted fetch 2026-11-07, returned 404, unverified: https://docs.getmaxim.ai/bifrost
- Streamlit Community Cloud, deploy: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- Streamlit Community Cloud, secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit free tier limits, secondary guides citing Streamlit docs, unverified on the official pages fetched: https://www.360digitaltransformation.com/blogs/guides/streamlit-tutorial-2026-build-your-first-data-app-free-tier-limits-and-when-not-to-use-it , https://livemy.app/blog/deploy-streamlit-app , https://miget.com/blog/streamlit-hosting
- Winning hackathon guides: https://www.tinyfish.ai/blog/how-to-win-a-hackathon-with-ai , https://www.masaischool.com/blog/how-to-win-an-ai-hackathon-in-2026-full-guide/ , https://hackathon-vault-ten.vercel.app/ , https://www.institutepm.com/knowledge-hub/ai-hackathon-playbook , https://hack4hack.com/hackathons/agentx-hackathon-2026-hooc
- Tavily 401 troubleshooting, secondary, DeepWiki: https://deepwiki.com/tavily-ai/tavily-mcp/9-troubleshooting
