#!/usr/bin/env python3
"""Simple web UI for the Tavily Research Agent, standard library only.

Why stdlib and not Streamlit/FastAPI here: this MVP must run with
only `pip install -r requirements.txt` (requests + reportlab) and
must not fail if a heavier web framework is missing. The web UI
reuses exactly the same briefing pipeline as the CLI, so it is not
a separate HTML-only demo.

Run:
    python3 web_ui.py --port 8000
Then open http://127.0.0.1:8000 in a browser.

Live mode needs TAVILY_API_KEY in the environment of the server
process. Tick "Mock mode" to run with local fixtures instead.
No key is ever written to disk by this server.
"""
from __future__ import annotations

import argparse
import html
import sys
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import load_fixtures
from tavily_agent.briefing import build_briefing
from tavily_agent.dates import meeting_window
from tavily_agent.render import render_markdown
from tavily_agent.tavily_client import search_all_categories

FORM = """<!doctype html><html><head><meta charset="utf-8"><title>Tavily Research Agent</title></head>
<body><h1>Tavily Research Agent</h1>
<p>One-page briefing before a meeting, from the last 30 days only. Every development carries its source link.</p>
<form method="post" action="/briefing">
<label>Company or person: <input name="subject" required size="40"></label><br><br>
<label>Meeting date: <input name="meeting" type="date" required></label><br><br>
<label><input type="checkbox" name="mock" value="1"> Mock mode (local fixtures, no Tavily key needed)</label><br><br>
<button type="submit">Build briefing</button>
</form>
<p>Live mode needs TAVILY_API_KEY set when you start this server. Mock mode needs no key.</p>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep server output quiet
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(FORM.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        fields = parse_qs(self.rfile.read(length).decode("utf-8"))
        subject = (fields.get("subject", [""])[0] or "").strip()
        meeting_text = (fields.get("meeting", [""])[0] or "").strip()
        mock = bool(fields.get("mock"))
        if not subject or not meeting_text:
            self._send("<p>Subject and meeting date are required. Go back and fill both in.</p>", 400)
            return
        try:
            meeting = date.fromisoformat(meeting_text)
        except ValueError:
            self._send("<p>Meeting date must be YYYY-MM-DD.</p>", 400)
            return
        start, end = meeting_window(meeting)
        try:
            if mock:
                raw = load_fixtures("examples/fixtures.json", subject)
                mode = "mock"
            else:
                raw = search_all_categories(subject, start.isoformat(), end.isoformat())
                mode = "live"
        except Exception as exc:
            self._send(f"<p>Search failed: {html.escape(str(exc))}</p>", 500)
            return
        briefing = build_briefing(subject, meeting, raw, mode=mode)
        md = render_markdown(briefing)
        body = "<h1>Briefing: " + html.escape(subject) + "</h1><pre>" + html.escape(md) + "</pre><p><a href='/'>Build another briefing</a></p>"
        self._send(body, 200)

    def _send(self, body: str, code: int):
        page = f"<!doctype html><html><head><meta charset='utf-8'></head><body>{body}</body></html>"
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Tavily Research Agent web UI: http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
