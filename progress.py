"""
TARRIFIC HOST BOT - Progress Message Builder
Option 5 style: Animated blocks with exact file tracking
"""
from config import HOSTING_STEPS, PROGRESS_BLOCKS

class ProgressBuilder:
    def __init__(self):
        self.b = PROGRESS_BLOCKS

    def build_progress(self, current_step, total_steps, percent, current_file=None, 
                       file_count=None, total_files=None, file_size=None, total_size=None,
                       status="in_progress", error=None, error_file=None):
        """
        Build the Option 5 progress display

        status: "in_progress", "done", "failed", "waiting"
        """
        lines = []
        lines.append("┌─────────────────────────────┐")

        if status == "failed":
            lines.append("│  ❌ DEPLOYMENT FAILED       │")
        elif status == "done":
            lines.append("│  ✅ DEPLOYMENT COMPLETE     │")
        else:
            lines.append("│  🚀 NEW SITE DEPLOYMENT     │")

        lines.append("│                             │")
        lines.append(f"│  Step {current_step}/{total_steps}                   │")

        # Build step indicators
        for i, step_name in enumerate(HOSTING_STEPS):
            step_num = i + 1
            if step_num < current_step:
                # Done
                bar = "████████████ DONE"
                symbol = self.b["done"]
            elif step_num == current_step:
                if status == "failed":
                    bar = "██████░░░░░░ FAILED"
                    symbol = self.b["failed"]
                elif status == "in_progress":
                    bar = "██████░░░░░░ IN PROGRESS"
                    symbol = self.b["in_progress"]
                else:
                    bar = "████████████ DONE"
                    symbol = self.b["done"]
            else:
                if status == "failed" and step_num > current_step:
                    bar = "░░░░░░░░░░░░ BLOCKED"
                    symbol = self.b["waiting"]
                else:
                    bar = "░░░░░░░░░░░░ WAITING"
                    symbol = self.b["waiting"]

            lines.append(f"│  [{step_name:13}] {bar} │")

        lines.append("│                             │")

        # Progress bar
        filled = int(percent / 10)
        bar = "▰" * filled + "▱" * (10 - filled)
        lines.append(f"│  {bar}  {percent}%           │")

        lines.append("│                             │")

        # Current action
        if status == "failed" and error:
            lines.append(f"│  🔴 ERROR at Step {current_step}/{total_steps}        │")
            lines.append(f"│  Location: {HOSTING_STEPS[current_step-1]:13} │")
            if error_file:
                lines.append(f"│  File: {error_file:21} │")
            lines.append("│                             │")
            lines.append(f"│  Message:                   │")
            # Wrap error message
            error_lines = self._wrap_text(error, 25)
            for el in error_lines:
                lines.append(f"│  {el:27} │")
        elif status == "done":
            lines.append("│  🌐 Your site is live:      │")
            if current_file:
                url_lines = self._wrap_text(current_file, 25)
                for ul in url_lines:
                    lines.append(f"│  {ul:27} │")
        else:
            if current_file:
                lines.append(f"│  Current: 📤 {current_file:14} │")
            if file_count and total_files:
                lines.append(f"│  {file_count}/{total_files} — {current_file[:18]:18} │")
            if file_size and total_size:
                lines.append(f"│  ({self._format_size(file_size)} / {self._format_size(total_size)} total) │")

        lines.append("└─────────────────────────────┘")

        return "
".join(lines)

    def _wrap_text(self, text, width):
        """Wrap text to fit in box"""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= width:
                current += " " + word if current else word
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _format_size(self, size_bytes):
        """Format bytes to human readable"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def build_menu(self, title, items, footer=None):
        """Build generic menu box"""
        lines = []
        lines.append("┌─────────────────────────────┐")
        lines.append(f"│  {title:25} │")
        lines.append("│                             │")

        for item in items:
            lines.append(f"│  {item:27} │")

        if footer:
            lines.append("│                             │")
            lines.append(f"│  {footer:27} │")

        lines.append("└─────────────────────────────┘")
        return "
".join(lines)

    def build_error(self, step, location, message, error_file=None):
        """Build error display"""
        return self.build_progress(
            current_step=step,
            total_steps=5,
            percent=(step - 1) * 20,
            status="failed",
            error=message,
            error_file=error_file
        )

    def build_success(self, url):
        """Build success display"""
        return self.build_progress(
            current_step=5,
            total_steps=5,
            percent=100,
            status="done",
            current_file=url
        )
