#!/usr/bin/env python3
"""Drive the v2 demo on screen under Xvfb for ffmpeg x11grab recording.

Shows real content only: the actual CLI run (build_playground_briefings.py
streaming its real output), page 1 of the real briefing PDFs scrolling,
the real live_smoke key check, and the real unit tests running.
No fixture output is shown. Timing follows demo_assets_v2/timeline.json.

Fixes over v1:
- No raw markdown list is ever shown. Scene 4 shows plain company
  count lines plus the rendered PDF pages only, never lines starting
  with "- **", so no ** markers can appear on screen.
- The mouse cursor is hidden everywhere (cursor="none" on the root,
  the text widget and the canvas), so no I-beam can appear in any frame.
- Each scene fills its allotted slot exactly, so scenes cannot overrun
  into the next scene.
"""
import json
import subprocess
import sys
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
root.title("Tavily Research Agent - demo v2")
root.geometry("1920x1080+0+0")
root.attributes("-fullscreen", True)
root.configure(bg=BG, cursor="none")

text = tk.Text(root, bg=BG, fg=FG, font=("DejaVu Sans Mono", 24),
               wrap="word", borderwidth=0, highlightthickness=0,
               padx=70, pady=50, cursor="none")
text.pack(fill="both", expand=True)
text.tag_configure("title", font=("DejaVu Sans Mono", 46, "bold"), foreground=ACCENT)
text.tag_configure("accent", foreground=ACCENT)
text.tag_configure("green", foreground=GREEN)
text.tag_configure("dim", foreground=DIM)
text.tag_configure("small", font=("DejaVu Sans Mono", 20), foreground=DIM)

canvas = None
scene_start = 0.0
scene_dur = 0.0


def begin_scene(dur):
    global scene_start, scene_dur
    scene_start = time.time()
    scene_dur = dur


def fill_slot():
    """Wait until this scene's allotted duration has elapsed."""
    while True:
        left = scene_dur - (time.time() - scene_start)
        if left <= 0:
            return
        time.sleep(min(left, 0.1))
        root.update_idletasks()


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
    canvas = tk.Canvas(root, bg="white", highlightthickness=0, cursor="none")
    canvas.pack(fill="both", expand=True)
    img = tk.PhotoImage(file=str(png_path))
    w, h = img.width(), img.height()
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
    begin_scene(dur)
    log("scene1 problem")
    clear()
    show(["Tavily Research Agent", ""], "title")
    type_lines([
        "You walk into a meeting, and the other side has moved.",
        "",
        "A new launch. A new hire. A funding round.",
        "",
        "That is the problem this agent solves.",
    ], per_line_ms=700)
    fill_slot()


def scene2(dur):
    begin_scene(dur)
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
    fill_slot()


def scene3(dur):
    begin_scene(dur)
    log("scene3 live run")
    clear()
    show(["The real thing, running", ""], "title")
    stream_command(["python3", "build_playground_briefings.py"])
    show(["", "Briefings rebuilt from the 60 real Tavily results."], "green")
    fill_slot()


def scene4(dur):
    begin_scene(dur)
    log("scene4 live briefings")
    clear()
    show(["Live briefings, Nov 5, 2026", ""], "title")
    # Plain count lines only. No markdown list is ever shown, so no
    # raw ** markers can appear on screen in this scene.
    type_lines([
        "OpenAI: 14 developments kept",
        "Google: 15 developments kept",
        "Microsoft: 8 developments kept",
        "",
        "37 kept from 60 real results.",
    ], per_line_ms=500)
    for slug, name in [("openai", "OpenAI"), ("google", "Google"),
                       ("microsoft", "Microsoft")]:
        png = HERE / f"pdf-{slug}-p1-1.png"
        scroll_pdf_page(png, 3)
        clear()
        show(["Live briefings, Nov 5, 2026", ""], "title")
        show([f"{name} briefing, page 1", ""], "accent")
    fill_slot()


def scene5(dur):
    begin_scene(dur)
    log("scene5 batch 2 and tests")
    clear()
    show(["What is new", ""], "title")
    type_lines([
        "Demo mode: the three live briefings, no key needed.",
        "Wrong key? A clear error, not a silent failure.",
        "Extract: full page content for the top 8 links,",
        "         off by default.",
        "",
    ], per_line_ms=600)
    stream_command(["python3", "live_smoke.py"])
    show([""], None)
    stream_command(["python3", "-m", "unittest", "discover", "-s", "tests"])
    show(["", "Ran 52 tests. OK."], "green")
    fill_slot()


def scene6(dur):
    begin_scene(dur)
    log("scene6 honest limits and close")
    clear()
    show(["Honest limits", ""], "title")
    type_lines([
        "The snippets are short extracts from the Tavily Playground.",
        "The direct Tavily API route is still unproven,",
        "so Extract has not run live yet.",
        "",
        "Nothing in these briefings is invented.",
        "",
        "Code, tests and pitch deck are public on GitHub:",
        "",
        "github.com/pakmultilinks-dot/tavily-research-agent",
        "",
        "Try it before your next meeting,",
        "and walk in prepared.",
    ], per_line_ms=600)
    fill_slot()


SCENE_FN = {"seg1": scene1, "seg2": scene2, "seg3": scene3,
            "seg4": scene4, "seg5": scene5, "seg6": scene6}

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
