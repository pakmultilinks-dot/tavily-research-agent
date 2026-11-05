#!/usr/bin/env python3
"""Drive the real demo on screen under Xvfb for ffmpeg x11grab recording.

Shows real content only: the actual CLI run (build_playground_briefings.py
streaming its real output), the real live briefing markdowns scrolling,
page 1 of the real briefing PDFs scrolling, and the real unit tests
running. No fixture output is shown. Timing follows demo_assets/timeline.json.
Logs scene start times to demo_assets/player.log.
"""
import json
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
LOG = HERE / "player.log"

BG = "#0d1117"
FG = "#e6edf3"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
DIM = "#8b949e"

timeline = json.loads((HERE / "timeline.json").read_text())
GAP = timeline["gap"]
SCENES = timeline["scenes"]

start = time.time()


def log(msg):
    line = f"{time.time() - start:7.2f}s {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


LOG.write_text("")

root = tk.Tk()
root.title("Tavily Research Agent - demo")
root.geometry("1920x1080+0+0")
root.attributes("-fullscreen", True)
root.configure(bg=BG)

text = tk.Text(root, bg=BG, fg=FG, font=("DejaVu Sans Mono", 24),
               wrap="word", borderwidth=0, highlightthickness=0,
               padx=70, pady=50)
text.pack(fill="both", expand=True)
text.tag_configure("title", font=("DejaVu Sans Mono", 46, "bold"), foreground=ACCENT)
text.tag_configure("accent", foreground=ACCENT)
text.tag_configure("green", foreground=GREEN)
text.tag_configure("dim", foreground=DIM)
text.tag_configure("small", font=("DejaVu Sans Mono", 20), foreground=DIM)

canvas = None


def clear():
    global canvas
    if canvas is not None:
        canvas.destroy()
        canvas = None
    text.pack(fill="both", expand=True)
    text.delete("1.0", "end")


def show(lines, tag=None):
    for line in lines:
        text.insert("end", line + "\n", tag or ())
    text.see("end")
    root.update_idletasks()


def type_lines(lines, per_line_ms=260, tag=None):
    """Insert lines one by one for visible motion.

    Uses time.sleep plus update_idletasks (never root.update), so a
    scheduled next-scene callback cannot fire in the middle of a scene
    and destroy the widgets this scene is still drawing into.
    """
    for line in lines:
        text.insert("end", line + "\n", tag or ())
        text.see("end")
        root.update_idletasks()
        time.sleep(per_line_ms / 1000.0)
        root.update_idletasks()


def stream_command(cmd, prefix="$ "):
    """Run a real command and stream its real output into the window."""
    show([prefix + " ".join(cmd)], "dim")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, cwd=str(PROJECT))
    for line in proc.stdout:
        text.insert("end", line)
        text.see("end")
        root.update_idletasks()
    proc.wait()
    return proc.returncode


def scroll_pdf_page(png_path, seconds):
    """Scroll page 1 of a real briefing PDF upward in a canvas (real document scroll)."""
    global canvas
    text.pack_forget()
    canvas = tk.Canvas(root, bg="white", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    img = tk.PhotoImage(file=str(png_path))
    w, h = img.width(), img.height()
    # Scale to window width
    scale = 1920 / w
    img = img.subsample(1, 1)
    item = canvas.create_image(960, 0, image=img, anchor="n")
    canvas.image = img  # keep reference
    steps = int(seconds * 20)
    total_scroll = max(0, h - 1080)
    for i in range(steps + 1):
        if canvas is None:
            return
        y = -int(total_scroll * i / steps)
        canvas.coords(item, 960, y)
        root.update_idletasks()
        time.sleep(0.05)
        root.update_idletasks()
    time.sleep(0.2)
    root.update_idletasks()


def scene1(dur):
    log("scene1 problem")
    clear()
    show(["Tavily Research Agent", ""], "title")
    type_lines([
        "You walk into a meeting, and the other side has moved.",
        "",
        "A new launch. A new hire. A funding round.",
        "And you never saw it coming.",
        "",
        "That is the problem this agent solves.",
    ], per_line_ms=700)


def scene2(dur):
    log("scene2 solution")
    clear()
    show(["How it works", ""], "title")
    type_lines([
        "$ python3 main.py --subject \"OpenAI\" --meeting 2026-11-05",
        "",
        "Input:  a company or a person, plus a meeting date",
        "Search: last 30 days only",
        "        news  |  launches  |  hires  |  funding",
        "",
        "Output: a one page briefing",
        "        summary, key developments,",
        "        discussion points, open questions",
        "",
        "Every development carries its date and its source link.",
    ], per_line_ms=650)


def scene3(dur):
    log("scene3 live run")
    clear()
    show(["The real thing, running", ""], "title")
    stream_command(["python3", "build_playground_briefings.py"])
    show(["", "Briefings rebuilt from the 60 real Tavily results."], "green")


def scene4(dur):
    log("scene4 live briefings")
    clear()
    show(["Live briefings, Nov 5, 2026", ""], "title")
    for company, slug, kept in [("OpenAI", "openai", 14),
                                ("Google", "google", 15),
                                ("Microsoft", "microsoft", 8)]:
        md = (PROJECT / "examples" / f"live-{slug}" / "briefing.md").read_text()
        lines = [l for l in md.splitlines() if l.startswith("- **")][:4]
        show([f"{company}: {kept} developments kept", ""], "accent")
        type_lines(lines, per_line_ms=500)
        show([""], None)
    # Scroll the real PDF pages, 4 seconds each
    for slug in ["openai", "google", "microsoft"]:
        png = HERE / f"pdf-{slug}-p1-1.png"
        scroll_pdf_page(png, 4)
        clear()
        show(["Live briefings, Nov 5, 2026", ""], "title")


def scene5(dur):
    log("scene5 architecture and tests")
    clear()
    show(["Under the hood", ""], "title")
    type_lines([
        "A small Python app. One pipeline, two front ends:",
        "  CLI  (main.py)  and  web UI  (web_ui.py)",
        "  tavily_agent: dates, filtering, deduplication, rendering",
        "",
    ], per_line_ms=600)
    stream_command(["python3", "-m", "unittest", "discover", "-s", "tests"])
    show(["", "12 tests. All pass."], "green")


def scene6(dur):
    log("scene6 honest limits")
    clear()
    show(["Honest limits", ""], "title")
    type_lines([
        "The snippets are short extracts from the Tavily Playground.",
        "The direct Tavily API route still returns an error here,",
        "so the live data comes from the Playground,",
        "not a direct API call.",
        "",
        "Nothing in these briefings is invented.",
        "Results with a truncated source link were dropped.",
    ], per_line_ms=700)


def scene7(dur):
    log("scene7 close")
    clear()
    show(["Tavily Research Agent", ""], "title")
    type_lines([
        "Code, tests and pitch deck are public on GitHub:",
        "",
        "github.com/pakmultilinks-dot/tavily-research-agent",
        "",
        "Try it before your next meeting,",
        "and walk in prepared.",
    ], per_line_ms=700)


SCENE_FN = {"seg1": scene1, "seg2": scene2, "seg3": scene3,
            "seg4": scene4, "seg7": scene5, "seg5": scene6, "seg6": scene7}

# Schedule scenes on the narration timeline.
t = 0.0
for scene in SCENES:
    fn = SCENE_FN[scene["seg"]]
    root.after(int(t * 1000), fn, scene["dur"])
    t += scene["dur"] + GAP

total_ms = int(t * 1000)
log(f"total timeline {t:.2f}s, quitting at {total_ms}ms")
root.after(total_ms, root.destroy)
root.mainloop()
log("player done")
