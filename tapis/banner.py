"""Banner CLI animasi menara BTS. Palet gelap."""
from __future__ import annotations

import time

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

NAMA = r"""
 ████████╗ █████╗ ██████╗ ██╗███████╗
 ╚══██╔══╝██╔══██╗██╔══██╗██║██╔════╝
    ██║   ███████║██████╔╝██║███████╗
    ██║   ██╔══██║██╔═══╝ ██║╚════██║
    ██║   ██║  ██║██║     ██║███████║
    ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
"""

TOWER = [
    "            .            ",
    "           /|\\           ",
    "          / | \\          ",
    "         /  |  \\         ",
    "            |            ",
    "       .-\"\"\"\"\"\"\"-.       ",
    "      /     |     \\      ",
    "     /      |      \\     ",
    "            |            ",
    "        .-\"\"\"\"\"-.        ",
    "       /   |   \\       ",
    "      /    |    \\      ",
    "           |           ",
    "      ____/_\\____      ",
]

FASE = [
    " (·)        ",
    " ((•))      ",
    "(((  )))    ",
    " ((•))      ",
    " (·)        ",
]

SUB = "project.m4zk1pL4y LlMs"
TAG = "Lawful Interception Management System  ·  Indonesia  ·  ETSI HI2/HI3"


def _bingkai(i: int) -> Group:
    gel = FASE[i % len(FASE)]
    baris = []
    for ln in TOWER:
        t = Text()
        t.append(ln, style="grey30")
        t.append("   ")
        t.append(gel, style="bold dark_cyan")
        baris.append(t)
    kepala = Text(NAMA.strip("\n"), style="bold grey70")
    sub = Text(SUB.center(38), style="grey37 italic")
    tag = Text(TAG, style="grey27")
    return Group(Align.center(kepala), Text(""), *[Align.center(b) for b in baris],
                 Text(""), Align.center(sub), Align.center(tag))


def tampilkan(console: Console | None = None, siklus: int = 12, jeda: float = 0.11) -> None:
    c = console or Console()
    with Live(_bingkai(0), console=c, refresh_per_second=12, transient=False) as live:
        for i in range(siklus):
            time.sleep(jeda)
            live.update(_bingkai(i))


def ringkas(console: Console | None = None) -> None:
    c = console or Console()
    c.print(Text("TAPIS", style="bold grey70"), Text("· "), Text(SUB, style="grey37 italic"))
