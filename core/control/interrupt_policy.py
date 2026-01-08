"""
Interrupt Policy Configuration
Day 18.4 — Intent-Aware Interrupt Handling

HARD   -> Immediate cancellation
SOFT   -> Ask user confirmation before cancelling
IGNORE -> Ignore interrupt completely
"""

from core.nlp.intent import Intent

INTERRUPT_POLICY = {
    # =========================
    # 🔴 HARD INTERRUPTS
    # =========================
    Intent.OPEN_BROWSER: "HARD",
    Intent.OPEN_TERMINAL: "HARD",
    Intent.OPEN_FILE: "HARD",
    Intent.OPEN_FILE_MANAGER: "HARD",

    # =========================
    # 🟡 SOFT INTERRUPTS
    # =========================
    Intent.SEARCH_WEB: "SOFT",
    Intent.LIST_FILES: "SOFT",

    # =========================
    # 🟢 IGNORE INTERRUPTS
    # =========================
    Intent.GREETING: "IGNORE",
    Intent.HELP: "IGNORE",
}
