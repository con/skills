#!/usr/bin/env python3
"""HTTP server for issue-triage web UI.

Serves a JSON API and static files for a single-page triage dashboard.
Uses only Python stdlib (http.server, json, subprocess, etc.).
"""

from __future__ import annotations

import argparse
import http.server
import json
import mimetypes
import os
import signal
import subprocess
import sys
import tempfile
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    """Load a JSON file, returning empty dict if missing."""
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_json(path: Path, data: dict) -> None:
    """Atomically write JSON to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.rename(path)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def mark_triaged(
    triage_dir: Path,
    number: int,
    action: str,
    comment_posted: bool = False,
    note: str = "",
) -> dict:
    """Record a triage decision in state.json and return the entry."""
    state_path = triage_dir / "state.json"
    state = load_json(state_path)
    if "triaged" not in state:
        state["triaged"] = {}
    entry: dict = {
        "action": action,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if comment_posted:
        entry["comment_posted"] = True
    if note:
        entry["note"] = note
    state["triaged"][str(number)] = entry
    save_json(state_path, state)
    return entry


# ---------------------------------------------------------------------------
# Request handler factory
# ---------------------------------------------------------------------------

def make_handler(triage_dir: Path, repo: str):
    """Create a request handler class bound to *triage_dir* and *repo*."""

    static_dir = Path(__file__).resolve().parent / "static"

    class Handler(http.server.BaseHTTPRequestHandler):

        def log_message(self, format, *args):  # noqa: A002
            """Suppress default access log noise."""
            pass

        # -- Response helpers -------------------------------------------------

        def _send_json(self, data: object, status: int = 200) -> None:
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_error_json(self, status: int, message: str) -> None:
            self._send_json({"error": message}, status)

        def _serve_static(self, file_path: str) -> None:
            """Serve a file from the static directory."""
            # Normalize and prevent directory traversal
            safe_path = os.path.normpath(file_path).lstrip("/")
            full_path = static_dir / safe_path

            # Ensure the resolved path is still inside static_dir
            try:
                full_path.resolve().relative_to(static_dir.resolve())
            except ValueError:
                self._send_error_json(403, "Forbidden")
                return

            if not full_path.is_file():
                self._send_error_json(404, "Not found")
                return

            content_type, _ = mimetypes.guess_type(str(full_path))
            if content_type is None:
                content_type = "application/octet-stream"

            data = full_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length", 0))
            return self.rfile.read(length)

        def _parse_route(self) -> tuple[str, dict]:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            flat = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
            return parsed.path, flat

        # -- GET routes -------------------------------------------------------

        def do_GET(self):  # noqa: N802
            path, params = self._parse_route()

            if path == "/":
                # Serve index.html
                self._serve_static("index.html")
            elif path == "/api/findings":
                self._handle_get_findings()
            elif path == "/api/state":
                self._handle_get_state()
            elif path.startswith("/api/issues/"):
                try:
                    number = int(path.split("/")[3])
                    self._handle_get_issue(number)
                except (ValueError, IndexError):
                    self._send_error_json(400, "Invalid issue number")
            elif path.startswith("/"):
                # Try to serve as static file
                self._serve_static(path.lstrip("/"))
            else:
                self._send_error_json(404, "Not found")

        # -- POST routes ------------------------------------------------------

        def do_POST(self):  # noqa: N802
            path, _ = self._parse_route()

            if path == "/api/action":
                self._handle_action()
            else:
                self._send_error_json(404, "Not found")

        # -- API handlers -----------------------------------------------------

        def _handle_get_findings(self) -> None:
            data = load_json(triage_dir / "findings.json")
            self._send_json(data)

        def _handle_get_state(self) -> None:
            data = load_json(triage_dir / "state.json")
            if "triaged" not in data:
                data["triaged"] = {}
            self._send_json(data)

        def _handle_get_issue(self, number: int) -> None:
            """Fetch full issue details via gh CLI."""
            try:
                result = subprocess.run(
                    [
                        "gh", "issue", "view", str(number),
                        "--repo", repo,
                        "--json", "number,title,body,comments,labels,state",
                    ],
                    capture_output=True, text=True, check=True, timeout=30,
                )
                data = json.loads(result.stdout)
                self._send_json(data)
            except subprocess.CalledProcessError as exc:
                self._send_error_json(
                    502, f"gh CLI error: {exc.stderr.strip()}"
                )
            except subprocess.TimeoutExpired:
                self._send_error_json(504, "gh CLI timed out")
            except json.JSONDecodeError:
                self._send_error_json(502, "Invalid JSON from gh CLI")

        def _handle_action(self) -> None:
            """Handle a triage action (close, comment, skip)."""
            try:
                body = json.loads(self._read_body())
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_error_json(400, "Invalid JSON body")
                return

            number = body.get("number")
            action = body.get("action")
            comment = body.get("comment", "")

            if not isinstance(number, int) or number <= 0:
                self._send_error_json(400, "Invalid issue number")
                return
            if action not in ("close", "close_wontfix", "comment", "skip"):
                self._send_error_json(
                    400,
                    "Action must be 'close', 'close_wontfix', 'comment', or 'skip'",
                )
                return

            labels = body.get("labels", [])

            if action == "close":
                self._do_close(number, comment, labels=labels)
            elif action == "close_wontfix":
                self._do_close(
                    number, comment,
                    reason="not planned",
                    labels=["wontfix"] + labels,
                )
            elif action == "comment":
                self._do_comment(number, comment)
            elif action == "skip":
                self._do_skip(number, comment)

        def _run_gh(self, args: list[str]) -> tuple[bool, str]:
            """Run a gh CLI command. Returns (success, error_message)."""
            try:
                subprocess.run(
                    args, check=True, capture_output=True, text=True, timeout=30
                )
                return True, ""
            except subprocess.CalledProcessError as exc:
                msg = exc.stderr.strip() if exc.stderr else str(exc)
                print(f"gh command failed: {msg}", file=sys.stderr)
                return False, msg
            except subprocess.TimeoutExpired:
                print("gh command timed out", file=sys.stderr)
                return False, "Command timed out"

        def _do_close(
            self,
            number: int,
            comment: str,
            reason: str = "completed",
            labels: list[str] | None = None,
        ) -> None:
            # Add labels if requested
            for label in labels or []:
                ok, err = self._run_gh([
                    "gh", "issue", "edit", str(number),
                    "--repo", repo, "--add-label", label,
                ])
                if not ok:
                    self._send_json(
                        {"ok": False, "error": f"Failed to add label '{label}': {err}"},
                        502,
                    )
                    return

            # Post comment if provided
            if comment.strip():
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".md", delete=False
                ) as f:
                    f.write(comment)
                    tmppath = f.name
                try:
                    ok, err = self._run_gh([
                        "gh", "issue", "comment", str(number),
                        "--repo", repo, "--body-file", tmppath,
                    ])
                finally:
                    os.unlink(tmppath)
                if not ok:
                    self._send_json(
                        {"ok": False, "error": f"Failed to post comment: {err}"},
                        502,
                    )
                    return

            # Close the issue
            ok, err = self._run_gh([
                "gh", "issue", "close", str(number),
                "--repo", repo, "--reason", reason,
            ])
            if not ok:
                self._send_json(
                    {"ok": False, "error": f"Failed to close issue: {err}"},
                    502,
                )
                return

            entry = mark_triaged(
                triage_dir, number, "closed",
                comment_posted=bool(comment.strip()),
            )
            self._send_json({"ok": True, "action": "closed", "entry": entry})

        def _do_comment(self, number: int, comment: str) -> None:
            if not comment.strip():
                self._send_error_json(400, "Comment cannot be empty")
                return

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False
            ) as f:
                f.write(comment)
                tmppath = f.name
            try:
                ok, err = self._run_gh([
                    "gh", "issue", "comment", str(number),
                    "--repo", repo, "--body-file", tmppath,
                ])
            finally:
                os.unlink(tmppath)

            if not ok:
                self._send_json(
                    {"ok": False, "error": f"Failed to post comment: {err}"},
                    502,
                )
                return

            entry = mark_triaged(
                triage_dir, number, "commented", comment_posted=True,
            )
            self._send_json(
                {"ok": True, "action": "commented", "entry": entry}
            )

        def _do_skip(self, number: int, note: str) -> None:
            entry = mark_triaged(triage_dir, number, "skipped", note=note)
            self._send_json({"ok": True, "action": "skipped", "entry": entry})

    return Handler


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Issue triage web UI server")
    parser.add_argument(
        "--triage-dir", type=Path, required=True,
        help="Path to triage data directory (contains findings.json, state.json)",
    )
    parser.add_argument(
        "--repo", help="OWNER/REPO (read from findings.json if omitted)"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Port (default: 8765)"
    )
    args = parser.parse_args()

    triage_dir = args.triage_dir.resolve()
    if not triage_dir.exists():
        print(f"Error: {triage_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    repo = args.repo
    if not repo:
        # Try findings.json first, then issues.json
        for fname in ("findings.json", "issues.json"):
            data = load_json(triage_dir / fname)
            repo = data.get("repo", "")
            if repo:
                break
    if not repo:
        print(
            "Error: --repo required (or findings.json/issues.json must contain repo)",
            file=sys.stderr,
        )
        sys.exit(1)

    handler_cls = make_handler(triage_dir, repo)
    server = http.server.ThreadingHTTPServer(("0.0.0.0", args.port), handler_cls)

    def shutdown(signum, frame):
        print("\nShutting down...")
        server.shutdown()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"Issue triage UI: http://127.0.0.1:{args.port}")
    print(f"Repo: {repo}")
    print(f"Data: {triage_dir}")
    server.serve_forever()


if __name__ == "__main__":
    main()
