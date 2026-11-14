"""
Zero-GPU Mobile Virtual Display for H4ck3rMx Emulator
Renders a responsive mobile screen in terminal ANSI/curses or memory buffer.
Avoids heavy GPU requirements and slow CPU shader rasterizers (e.g. SwiftShader/lavapipe).
"""

import sys
import time
from typing import List, Optional


class VirtualMobileScreen:
    """A lightweight virtual mobile screen renderer."""

    def __init__(self, width: int = 54, height: int = 24):
        self.width = width
        self.height = height
        self.buffer: List[List[str]] = [[" " for _ in range(width)] for _ in range(height)]
        self.status_bar_data = {
            "battery": 85,
            "signal": "5G-SEC",
            "tor": True,
            "peers": 4,
            "agent": "W1z4rDV1510n",
        }

    def clear(self):
        self.buffer = [[" " for _ in range(self.width)] for _ in range(self.height)]

    def draw_text(self, x: int, y: int, text: str, max_len: Optional[int] = None):
        if y < 0 or y >= self.height:
            return
        if max_len is not None:
            text = text[:max_len]
        for i, ch in enumerate(text):
            col = x + i
            if 0 <= col < self.width:
                self.buffer[y][col] = ch

    def draw_box(self, x1: int, y1: int, x2: int, y2: int, title: str = ""):
        # Borders
        for x in range(x1, x2 + 1):
            if 0 <= x < self.width:
                if 0 <= y1 < self.height:
                    self.buffer[y1][x] = "-"
                if 0 <= y2 < self.height:
                    self.buffer[y2][x] = "-"
        for y in range(y1, y2 + 1):
            if 0 <= y < self.height:
                if 0 <= x1 < self.width:
                    self.buffer[y][x1] = "|"
                if 0 <= x2 < self.width:
                    self.buffer[y][x2] = "|"
        # Corners
        if 0 <= x1 < self.width and 0 <= y1 < self.height:
            self.buffer[y1][x1] = "+"
        if 0 <= x2 < self.width and 0 <= y1 < self.height:
            self.buffer[y1][x2] = "+"
        if 0 <= x1 < self.width and 0 <= y2 < self.height:
            self.buffer[y2][x1] = "+"
        if 0 <= x2 < self.width and 0 <= y2 < self.height:
            self.buffer[y2][x2] = "+"

        if title and 0 <= y1 < self.height:
            t = f" {title} "
            start_x = x1 + 2
            self.draw_text(start_x, y1, t, max_len=x2 - x1 - 4)

    def render_frame(self, active_content: List[str]) -> str:
        self.clear()
        # Outer phone bezel
        self.draw_box(0, 0, self.width - 1, self.height - 1, "H4ck3rMx Mobile")

        # Top mobile status bar
        tor_str = "[ONION:ON]" if self.status_bar_data["tor"] else "[ONION:OFF]"
        bar = (
            f" {self.status_bar_data['signal']} | "
            f"BAT:{self.status_bar_data['battery']}% | "
            f"{tor_str} | "
            f"HEX:{self.status_bar_data['peers']} | "
            f"{time.strftime('%H:%M')}"
        )
        self.draw_text(2, 1, bar, max_len=self.width - 4)
        for x in range(1, self.width - 1):
            self.buffer[2][x] = "="

        # Content area (terminal or UI lines)
        content_y = 3
        max_lines = self.height - 6
        for line in active_content[-max_lines:]:
            self.draw_text(2, content_y, line, max_len=self.width - 4)
            content_y += 1

        # Bottom Agent status bar
        agent_y = self.height - 3
        for x in range(1, self.width - 1):
            self.buffer[agent_y][x] = "="
        agent_status = f" [AI: {self.status_bar_data['agent']} - Hebbian CPU Core ACTIVE] "
        self.draw_text(2, agent_y + 1, agent_status, max_len=self.width - 4)

        # Output to string
        return "\n".join("".join(row) for row in self.buffer)
