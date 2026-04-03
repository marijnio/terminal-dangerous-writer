#!/usr/bin/env python3
"""
Dangerous Writer — a terminal writing app that deletes everything
if you stop typing for too long. Press Ctrl+C to quit and save.
"""

import sys, time, threading, os, termios, tty, signal, re

# ── Configuration ──────────────────────────────────────────────
TIMEOUT      = 5.0   # seconds of silence before deletion
WARN_AT      = 2.0   # seconds before deletion to start warning
SAVE_ON_EXIT = True  # Ctrl+C saves to file
OUTPUT_FILE  = "dangerous_output.txt"
# ───────────────────────────────────────────────────────────────

RESET        = "\033[0m"
BOLD         = "\033[1m"
RED          = "\033[31m"
YELLOW       = "\033[33m"
GREEN        = "\033[32m"
HIDE_CURSOR  = "\033[?25l"
SHOW_CURSOR  = "\033[?25h"

def move(row, col=1):
    return f"\033[{row};{col}H"

def clear_line():
    return "\033[2K"

def clear_screen():
    return "\033[2J" + move(1)

_ANSI_RE = re.compile(r"\033\[[0-9;]*[A-Za-z]")
def visible_len(s):
    return len(_ANSI_RE.sub("", s))

# Shared state
text          = []
last_keypress = time.time()
lock          = threading.Lock()
running       = True


def term_size():
    try:
        sz = os.get_terminal_size()
        return sz.columns, sz.lines
    except OSError:
        return 80, 24


def build_status_bar(time_left: float, word_count: int) -> str:
    cols, _ = term_size()

    if time_left <= WARN_AT:
        colour = RED
        label  = f"!! DANGER !!  |  {time_left:.1f}s  |  {word_count} words  |  Ctrl+C to save & quit"
    else:
        colour = GREEN if time_left > TIMEOUT * 0.6 else YELLOW
        label  = f"keep going  |  {time_left:.1f}s  |  {word_count} words  |  Ctrl+C to save & quit"

    # Pad/truncate by VISIBLE length only
    vis = len(label)
    if vis < cols:
        label = label + " " * (cols - vis)
    else:
        label = label[:cols]

    return f"\033[7m{colour}{BOLD}{label}{RESET}"


def wrap_text(content: str, width: int) -> list:
    out = []
    for para in content.split("\n"):
        if not para:
            out.append("")
            continue
        words = para.split(" ")
        line  = ""
        for word in words:
            if not word:
                continue
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= width:
                line += " " + word
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def render(time_left: float, flash_msg: str = ""):
    cols, rows = term_size()
    content    = "".join(text)
    words      = len(content.split()) if content.strip() else 0

    buf = []

    # Row 1: status bar (pure visible-length padding, no ANSI in label)
    buf.append(move(1) + clear_line() + build_status_bar(time_left, words))

    # Row 2: blank or flash
    if flash_msg:
        msg = flash_msg[:cols]
        buf.append(move(2) + clear_line() + f"{RED}{BOLD}{msg}{RESET}")
    else:
        buf.append(move(2) + clear_line())

    # Rows 3+: text
    lines     = wrap_text(content, cols)
    text_rows = rows - 3
    visible   = lines[-text_rows:] if len(lines) > text_rows else lines

    for i, line in enumerate(visible):
        buf.append(move(3 + i) + clear_line() + line)

    for row in range(3 + len(visible), rows + 1):
        buf.append(move(row) + clear_line())

    sys.stdout.write("".join(buf))
    sys.stdout.flush()


def timer_thread():
    global text, last_keypress, running

    while running:
        time.sleep(0.1)
        with lock:
            elapsed   = time.time() - last_keypress
            time_left = max(0.0, TIMEOUT - elapsed)

            if elapsed >= TIMEOUT and text:
                text = []
                for i in range(6):
                    msg = "  !! EVERYTHING DELETED !!  " if i % 2 == 0 else ""
                    render(0.0, flash_msg=msg)
                    time.sleep(0.12)
                last_keypress = time.time()
            else:
                render(time_left)


def read_char(fd) -> str:
    return os.read(fd, 1).decode("utf-8", errors="replace")


def main():
    global running, last_keypress, text

    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)

    def cleanup(signum=None, frame=None):
        global running
        running = False
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        sys.stdout.write(clear_screen() + SHOW_CURSOR)
        sys.stdout.flush()
        content = "".join(text)
        if SAVE_ON_EXIT and content.strip():
            with open(OUTPUT_FILE, "w") as f:
                f.write(content)
            print(f"{GREEN}Saved to {OUTPUT_FILE}{RESET}")
        else:
            print(f"{YELLOW}Nothing to save.{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT,  cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        tty.setraw(fd)
        sys.stdout.write(HIDE_CURSOR + clear_screen())
        sys.stdout.flush()

        t = threading.Thread(target=timer_thread, daemon=True)
        t.start()

        while running:
            ch = read_char(fd)

            if ch in ("\x03", "\x04"):
                break

            with lock:
                if ch == "\x7f":
                    if text:
                        text.pop()
                elif ch == "\r":
                    text.append("\n")
                elif ch >= " " or ch == "\t":
                    text.append(ch)

                last_keypress = time.time()

    finally:
        cleanup()


if __name__ == "__main__":
    main()
