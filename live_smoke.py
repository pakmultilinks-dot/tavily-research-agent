#!/usr/bin/env python3
"""Live smoke check for the direct Tavily API route.

Runs one small search (max_results 1) with the key from
TAVILY_API_KEY and reports the HTTP status only. It writes no
files and prints no key value. Use it to check a fresh key
before running a full live briefing.

Usage:
    export TAVILY_API_KEY="your-key-here"
    python3 live_smoke.py

Exit code 0 means Tavily answered with results. Exit code 2
means the key was rejected with HTTP 401, and the printed
message names the fix. Exit code 1 means any other failure
(timeout after one retry, missing key, or another HTTP error).

Live status: unproven as of 2026-11-07. Calls from this
environment returned HTTP 401 with the stored credential,
while the same key works in the Tavily Playground. See
LIVE_TEST.md. Do not guess a key. Do not put a key in code.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tavily_agent.tavily_client import TavilyAuthError, smoke_check


def main() -> int:
    try:
        result = smoke_check()
    except TavilyAuthError as exc:
        print(f"SMOKE FAILED: {exc}")
        return 2
    except RuntimeError as exc:
        print(f"SMOKE FAILED: {exc}")
        return 1
    print(f"SMOKE OK: Tavily answered, {result['results']} result(s) returned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
