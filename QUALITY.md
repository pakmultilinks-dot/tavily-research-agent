Tavily Research Agent, briefing quality report
Measured: 2026-11-07
Source: examples/live-playground-2026-11-05.json (60 transcribed Tavily Playground results, Nov 5, 2026)
Reproduce: python3 quality_report.py
Method: each company rebuilt through the same pipeline and honesty drops as build_playground_briefings.py. Numbers below are measured from that rebuild and cross-checked against the committed briefing Markdown headers.

Per company
OpenAI: total 20, kept 14, dropped as truncated URL 1, profile page 3, duplicates 2, too old 0
  dated result: 14/14 (100%)
  with source URL: 14/14 (100%)
  title and snippet both name the subject: 10/14 (71%)
  date range covered: 2026-10-08 to 2026-11-04
  categories covered: funding, deals and partnerships, hires and leadership, launches and product updates, news (4 of 4)
  with full content (Tavily Extract): 0/14 (0%)
Google: total 20, kept 15, dropped as truncated URL 5, profile page 0, duplicates 0, too old 0
  dated result: 15/15 (100%)
  with source URL: 15/15 (100%)
  title and snippet both name the subject: 4/15 (27%)
  date range covered: 2026-10-08 to 2026-11-04
  categories covered: funding, deals and partnerships, hires and leadership, launches and product updates, news (4 of 4)
  with full content (Tavily Extract): 0/15 (0%)
Microsoft: total 20, kept 8, dropped as truncated URL 10, profile page 2, duplicates 0, too old 0
  dated result: 8/8 (100%)
  with source URL: 8/8 (100%)
  title and snippet both name the subject: 4/8 (50%)
  date range covered: 2026-10-20 to 2026-11-04
  categories covered: funding, deals and partnerships, hires and leadership, launches and product updates, news (4 of 4)
  with full content (Tavily Extract): 0/8 (0%)

Total
Total: total 60, kept 37, dropped as truncated URL 16, profile page 5, duplicates 2, too old 0
  dated result: 37/37 (100%)
  with source URL: 37/37 (100%)
  title and snippet both name the subject: 18/37 (49%)
  date range covered: 2026-10-08 to 2026-11-04
  categories covered: funding, deals and partnerships, hires and leadership, launches and product updates, news (4 of 4)
  with full content (Tavily Extract): 0/37 (0%)

Cross-check against the committed briefing Markdown headers
  OpenAI: kept and dropped counts match the rebuild: yes
  Google: kept and dropped counts match the rebuild: yes
  Microsoft: kept and dropped counts match the rebuild: yes

Limits, read before judging
  The named-subject share is low mainly because the Playground JSON view truncates snippets at about 100 characters, so a snippet often does not name the subject even when the title does. Those developments are still listed in full, with source links, in Key developments; only the Top findings quote the named ones. Tavily Extract (off by default) can add full content for the top 8 developments per company, but it has not been run live yet, so with_full_content is 0 here. The direct API route is still unproven (HTTP 401 here), so these numbers measure the Playground briefings, not a live API run.
