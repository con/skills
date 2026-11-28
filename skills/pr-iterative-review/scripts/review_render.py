#!/usr/bin/env python3
"""Render, check and find the reviews of the pr-iterative-review skill.

Standard library only; it never contacts GitHub. The agent running a
review writes the reconciled findings as JSON (the format is in
SKILL.md, with a complete example in references/findings-example.json).
This script turns them into the one layout every review uses, checks
each inline comment against the diff it will be posted on, and finds
the review this skill last posted on a pull request.

Subcommands
-----------
render    FINDINGS.json --out DIR [--diff DIFF] [options]
          Write DIR/review.md (the review as a person will read it,
          with the inline comments listed at the end) and, for a pull
          request, DIR/payload.json (the request body for
          POST /repos/OWNER/REPO/pulls/N/reviews). --diff is the diff
          the review will be posted on, required for a pull request.
          `render --help` describes the other options.
previous  REVIEWS.json --user-id ID [--head-sha SHA]
          Print as JSON the latest review this skill posted from
          account ID, or null when there is none; with --head-sha,
          also whether that review was made at SHA.

Exit status: 0 on success, 2 when the input is unusable. The message
names every problem, so the findings can be corrected and rendered
again.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

SCHEMA = 1
TIERS = ("blocking", "should-fix", "optional", "nit")
TIER_HEADINGS = {
    "blocking": "Blocking",
    "should-fix": "Should fix",
    "optional": "Optional",
    "nit": "Nits",
}
TIER_LABELS = {
    "blocking": "Blocking",
    "should-fix": "Should fix",
    "optional": "Optional",
    "nit": "Nit",
}
PREVIOUS_STATUSES = {
    "fixed": "Fixed",
    "still-open": "Still open",
    "declined": "Declined",
    "withdrawn": "Withdrawn",
}
# The agent that coordinated the review; it may confirm a finding
# against the code.
LEAD = "lead"
SIDES = ("RIGHT", "LEFT")
EVENTS = ("comment", "request-changes")  # never an approval
# GitHub refuses review and comment bodies over 65536 characters.
MAX_BODY = 65000
MAX_REVIEWERS = 6

FINDINGS_KEYS = {
    "schema",
    "repo",
    "pr",
    "head_sha",
    "domains",
    "reviewers",
    "rounds",
    "summary",
    "ci",
    "findings",
    "previous",
    "checked",
    "ran",
    "not_checked",
}
FINDING_KEYS = {
    "tier",
    "title",
    "body",
    "path",
    "line",
    "start_line",
    "side",
    "suggestion",
    "confirmed_by",
    "thread_url",
}
REVIEWER_KEYS = {"id", "focus"}
PREVIOUS_KEYS = {"sha", "url", "items"}
PREVIOUS_ITEM_KEYS = {"title", "status", "note"}

_MARKER = re.compile(
    r"^<!-- pr-iterative-review v(?P<version>[0-9]+\.[0-9]+\.[0-9]+|unknown) "
    r"sha=(?P<sha>[0-9a-f]{40}) -->\r?$",
    re.MULTILINE,
)
_SHA = re.compile(r"[0-9a-f]{40}")
_REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_ID = re.compile(r"[a-z][a-z0-9-]{0,30}")
_SOURCE = re.compile(
    r"(?:con/skills@)?[0-9a-f]{7,40}(?:\+dirty)?|source commit unknown"
)
_THREAD = re.compile(
    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+"
    r"#discussion_r[0-9]+"
)
_REVIEW_URL = re.compile(
    r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+"
    r"#pullrequestreview-[0-9]+"
)
_VERSION = re.compile(
    r"^version:\s*([\"']?)([0-9]+\.[0-9]+\.[0-9]+)\1\s*(?:#.*)?$", re.MULTILINE
)
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
# A fence opener as CommonMark reads it: a backtick fence's info string
# holds no backtick. Only a fence at column 0 counts as code here: an
# indented one may sit in a list item and end with it.
_FENCE = re.compile(r"^(`{3,}(?!.*`)|~{3,})")
# What takes a backtick out of play (a backslash escape, a URL that
# GitHub links), or an inline code span, which closes only on a backtick
# run of the same length.
_INLINE_CODE = re.compile(
    r"\\.|<[A-Za-z][A-Za-z0-9+.-]+:[^\s<>]*>|(?:https?://|www\.)[^\s<]*|"
    r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)"
)
# A GitHub @-mention outside code, as a best effort: this is a second
# layer behind the reviewers' rule to mention nobody, not a Markdown
# parser. Only an ASCII letter or digit before it, as in an e-mail
# address, rules it out: GitHub looks for mentions in the rendered text,
# where `_@octocat_` is emphasis around a bare @octocat, and a letter
# such as an accented one may not count.
_MENTION = re.compile(
    r"(?<![A-Za-z0-9])@[A-Za-z0-9][A-Za-z0-9-]{0,38}(?:/[A-Za-z0-9_.-]+)?"
)
# Line ends as CommonMark reads them. str.splitlines() also splits on
# characters such as a form feed, which Markdown keeps inside a line.
_LINE_END = re.compile(r"\r\n?|\n")
# An image makes every viewer's browser, through GitHub's proxy, request
# its URL from another host.
_IMAGE = re.compile(r"!\[")
# Raw HTML that Markdown passes through (tags, comments, declarations):
# it can hide text from people.
_HTML = re.compile(
    r"<!--|<\?|<![A-Za-z]|<!\[CDATA\[|</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>"
)
# A link reference definition renders as nothing: its text reaches
# agents reading the API, not people.
_LINK_DEFINITION = re.compile(r"^[ \t]*\[[^\]\n]+\]:", re.MULTILINE)
# Credentials a review must never quote, in code or not.
_CREDENTIALS = (
    (
        "a GitHub token",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"
        ),
    ),
    ("an AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("a Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("an Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("a private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_ESCAPES = {
    "a": 7,
    "b": 8,
    "t": 9,
    "n": 10,
    "v": 11,
    "f": 12,
    "r": 13,
    '"': 34,
    "\\": 92,
}


class InputError(Exception):
    """The input cannot be used; the message says what to fix."""


# ----------------------------------------------------------------------
# Reading
# ----------------------------------------------------------------------


def load_json(path: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise InputError(f"{path}: not valid JSON ({error})") from error


def pages(document: object) -> list:
    """One list from the pages of `gh api --paginate --slurp`."""
    if not isinstance(document, list):
        raise InputError(
            "expected a JSON list (save every page with --paginate --slurp)"
        )
    if document and all(isinstance(page, list) for page in document):
        return [item for page in document for item in page]
    return document


def skill_version(skill_dir: Path) -> str:
    """This skill's version, from the apm.yml beside SKILL.md."""
    try:
        text = (skill_dir / "apm.yml").read_text(encoding="utf-8")
    except OSError:
        return "unknown"
    match = _VERSION.search(text)
    return match.group(2) if match else "unknown"


# ----------------------------------------------------------------------
# The diff a review is posted on
# ----------------------------------------------------------------------


def _unquote(value: str) -> str:
    """Decode a path that git printed in C-style quotes.

    Git quotes a path with special characters: "b/caf\\303\\251.md".
    """
    body = value[1 : value.rindex('"')] if value.count('"') >= 2 else None
    if body is None:
        raise InputError(f"diff: unterminated quoted path {value!r}")
    out = bytearray()
    index = 0
    while index < len(body):
        char = body[index]
        if char != "\\":
            out += char.encode("utf-8")
            index += 1
        elif body[index + 1 : index + 2] in _ESCAPES:
            out.append(_ESCAPES[body[index + 1]])
            index += 2
        elif re.fullmatch(r"[0-7]{3}", body[index + 1 : index + 4]):
            out.append(int(body[index + 1 : index + 4], 8))
            index += 4
        else:
            raise InputError(f"diff: unknown escape in quoted path {value!r}")
    return out.decode("utf-8", errors="replace")


def _diff_path(value: str, prefix: str) -> str | None:
    value = (
        _unquote(value) if value.startswith('"') else value.split("\t", 1)[0]
    )
    if value == "/dev/null":
        return None
    if not value.startswith(prefix):
        raise InputError(
            f"diff: path {value!r} lacks the {prefix!r} prefix; generate the"
            " diff with --src-prefix=a/ --dst-prefix=b/"
        )
    return value[len(prefix) :]


def parse_diff(text: str) -> dict[str, dict[str, dict[int, int]]]:
    """Map each file in a unified diff to the lines a comment can go on.

    Returns {path: {"RIGHT": {line: hunk}, "LEFT": {line: hunk}}}: the
    new-side numbers of added and context lines, the old-side numbers
    of removed and context lines, each with the index of its hunk,
    since a comment spanning several lines must stay within one hunk.
    A deleted file is keyed by its old path. Hunk bodies are read by
    their line counts, so a removed line that reads "-- x" is not taken
    for a file header. Lines are split on newlines only: a form feed or
    a Unicode line separator inside a changed line is part of that
    line.
    """
    files: dict[str, dict[str, dict[int, int]]] = {}
    current: dict[str, dict[int, int]] | None = None
    old_path: str | None = None
    hunk = 0
    old_no = new_no = old_left = new_left = 0
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for raw in lines:
        if old_left > 0 or new_left > 0:
            tag = raw[:1]
            if tag == "\\":
                continue
            if tag == "+" and new_left > 0:
                current["RIGHT"][new_no] = hunk
                new_no, new_left = new_no + 1, new_left - 1
            elif tag == "-" and old_left > 0:
                current["LEFT"][old_no] = hunk
                old_no, old_left = old_no + 1, old_left - 1
            elif tag in (" ", "", "\r") and old_left > 0 and new_left > 0:
                current["RIGHT"][new_no] = hunk
                current["LEFT"][old_no] = hunk
                new_no, new_left = new_no + 1, new_left - 1
                old_no, old_left = old_no + 1, old_left - 1
            else:
                raise InputError(
                    f"diff: line does not fit its hunk header: {raw[:80]!r}"
                )
            continue
        if raw.startswith("diff --git "):
            current, old_path = None, None
        elif raw.startswith("--- "):
            old_path = _diff_path(raw[4:].rstrip("\r"), "a/")
        elif raw.startswith("+++ "):
            new_path = _diff_path(raw[4:].rstrip("\r"), "b/")
            key = new_path if new_path is not None else old_path
            if key is None:
                raise InputError(
                    "diff: a file header names /dev/null on both sides"
                )
            current = files.setdefault(key, {"RIGHT": {}, "LEFT": {}})
        elif raw.startswith("@@"):
            match = _HUNK.match(raw)
            if not match or current is None:
                raise InputError(
                    "diff: hunk header outside a file or unreadable:"
                    f" {raw[:80]!r}"
                )
            hunk += 1
            old_no, old_left = int(match.group(1)), int(match.group(2) or "1")
            new_no, new_left = int(match.group(3)), int(match.group(4) or "1")
    if old_left > 0 or new_left > 0:
        raise InputError("diff: ends inside a hunk; the diff is truncated")
    return files


# ----------------------------------------------------------------------
# Checking the findings
# ----------------------------------------------------------------------


def _prose(text: str) -> tuple[str, bool]:
    """The text, with fenced code blocks and code spans removed.

    The flag is true when a fence is still open at the end.
    """
    kept: list[str] = []
    fence = ""
    for line in _LINE_END.split(text):
        if fence:
            stripped = line.strip()
            if (
                stripped
                and set(stripped) == {fence[0]}
                and len(stripped) >= len(fence)
            ):
                fence = ""
            continue
        match = _FENCE.match(line)
        if match:
            fence = match.group(1)
            continue
        kept.append(
            _INLINE_CODE.sub(
                lambda m: (
                    " " if m.group(1) or m.group(0) == "\\`" else m.group(0)
                ),
                line,
            )
        )
    return "\n".join(kept), bool(fence)


def _text(
    errors: list[str],
    where: str,
    value: object,
    *,
    required: bool = True,
    one_line: bool = False,
    limit: int = 20000,
) -> None:
    if value is None:
        if required:
            errors.append(f"{where}: missing")
        return
    if not isinstance(value, str):
        errors.append(f"{where}: must be a string")
        return
    if not value.strip():
        errors.append(f"{where}: empty")
        return
    if one_line and ("\n" in value or "\r" in value):
        errors.append(f"{where}: must be one line")
    if len(value) > limit:
        errors.append(f"{where}: longer than {limit} characters")
    prose, unclosed = _prose(value)
    if unclosed:
        errors.append(
            f"{where}: a code fence is opened but never closed, so it would"
            " pair with a fence in a later part of the review"
        )
    if "<!--" in prose:
        errors.append(
            f"{where}: HTML comments are not allowed outside code; they hide"
            " text from the reader and could imitate this skill's marker"
        )
    elif _HTML.search(prose):
        errors.append(
            f"{where}: raw HTML is not allowed outside code, since it can hide"
            " text from the reader; put code such as `List<int>` in backticks"
        )
    if _LINK_DEFINITION.search(prose):
        errors.append(
            f"{where}: a link reference definition renders as nothing, so its"
            " text would be hidden from people; write links inline"
        )
    if _IMAGE.search(prose):
        errors.append(
            f"{where}: images are not allowed; displaying one sends a request,"
            " with whatever its URL carries, to another host"
        )
    if "`" in prose:
        errors.append(
            f"{where}: a backtick without its pair on the same line would pair"
            " with a later one and turn code into text; close the code span,"
            " or write a literal backtick as \\`"
        )
    # Both forms: an entity such as &#64; renders as @, while text that
    # Python decodes and Markdown does not (an escaped &) must not hide
    # what stands before an @.
    mention = _MENTION.search(prose) or _MENTION.search(html.unescape(prose))
    if mention:
        errors.append(
            f"{where}: {mention.group(0)!r} would notify that account; put"
            " code such as a decorator in backticks and refer to people by"
            " their role (the author)"
        )
    _credentials(errors, where, value)


def _credentials(errors: list[str], where: str, value: str) -> None:
    for kind, pattern in _CREDENTIALS:
        if pattern.search(value):
            errors.append(
                f"{where}: contains what looks like {kind}; never quote a"
                " secret, cite where it is"
            )


def _text_list(errors: list[str], where: str, value: object) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(f"{where}: must be a list of strings")
        return
    for index, item in enumerate(value):
        _text(errors, f"{where}[{index}]", item, one_line=True, limit=500)


def _unknown(
    errors: list[str], where: str, value: dict, allowed: set[str]
) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{where}: unknown field {key!r}")


def _positive(value: object) -> bool:
    return (
        isinstance(value, int) and not isinstance(value, bool) and value >= 1
    )


def check_findings(data: object) -> list[str]:
    """Every problem with a findings document.

    An empty list means the document can be rendered.
    """
    if not isinstance(data, dict):
        return ["findings: the document must be a JSON object"]
    errors: list[str] = []
    _unknown(errors, "findings", data, FINDINGS_KEYS)
    if data.get("schema") != SCHEMA:
        errors.append(f"schema: must be {SCHEMA}")
    repo, pr = data.get("repo"), data.get("pr")
    if (repo is None) != (pr is None):
        errors.append(
            "repo and pr: give both for a pull request, or neither for a local"
            " review"
        )
    if repo is not None and not (
        isinstance(repo, str) and _REPO.fullmatch(repo)
    ):
        errors.append("repo: must be OWNER/REPO")
    if pr is not None and not _positive(pr):
        errors.append("pr: must be a pull request number")
    if not (
        isinstance(data.get("head_sha"), str)
        and _SHA.fullmatch(data["head_sha"])
    ):
        errors.append(
            "head_sha: must be the full 40-character commit id that was"
            " reviewed"
        )
    domains = data.get("domains", [])
    if not (
        isinstance(domains, list)
        and all(isinstance(d, str) and _ID.fullmatch(d) for d in domains)
    ):
        errors.append(
            "domains: must be a list of lens names such as 'backend' or"
            " 'ci-infra'"
        )

    reviewer_ids: list[str] = []
    reviewers = data.get("reviewers")
    if not (
        isinstance(reviewers, list) and 2 <= len(reviewers) <= MAX_REVIEWERS
    ):
        errors.append(
            f"reviewers: must list 2 to {MAX_REVIEWERS} reviewers, since a"
            " review is their cross-check"
        )
        reviewers = reviewers if isinstance(reviewers, list) else []
    for index, reviewer in enumerate(reviewers):
        where = f"reviewers[{index}]"
        if not isinstance(reviewer, dict):
            errors.append(f"{where}: must be an object with id and focus")
            continue
        _unknown(errors, where, reviewer, REVIEWER_KEYS)
        rid = reviewer.get("id")
        if not (isinstance(rid, str) and _ID.fullmatch(rid)) or rid == LEAD:
            errors.append(
                f"{where}.id: must be a short lowercase name other than"
                f" {LEAD!r}"
            )
        elif rid in reviewer_ids:
            errors.append(f"{where}.id: {rid!r} is listed twice")
        else:
            reviewer_ids.append(rid)
        _text(
            errors,
            f"{where}.focus",
            reviewer.get("focus"),
            one_line=True,
            limit=120,
        )
    rounds = data.get("rounds")
    if not (_positive(rounds) and rounds <= 3):
        errors.append(
            "rounds: must be 1 (round 1 found nothing), 2 (a cross-check) or 3"
            " (with rebuttals)"
        )
    elif rounds == 1 and data.get("findings"):
        errors.append(
            "rounds: a finding is confirmed in round 2, so a review with"
            " findings has at least 2"
        )
    _text(errors, "summary", data.get("summary"), limit=4000)
    _text(
        errors, "ci", data.get("ci"), required=False, one_line=True, limit=300
    )
    for key in ("checked", "ran", "not_checked"):
        _text_list(errors, key, data.get(key))

    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append(
            "findings: must be a list (empty when nothing was found)"
        )
        findings = []
    confirmers = set(reviewer_ids) | {LEAD}
    for index, finding in enumerate(findings):
        where = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{where}: must be an object")
            continue
        _unknown(errors, where, finding, FINDING_KEYS)
        if finding.get("tier") not in TIERS:
            errors.append(f"{where}.tier: must be one of {', '.join(TIERS)}")
        _text(
            errors,
            f"{where}.title",
            finding.get("title"),
            one_line=True,
            limit=120,
        )
        _text(errors, f"{where}.body", finding.get("body"))
        path, line, start = (
            finding.get("path"),
            finding.get("line"),
            finding.get("start_line"),
        )
        if path is not None and not (
            isinstance(path, str)
            and path.strip()
            and not _CONTROL.search(path)
            and not path.startswith("/")
        ):
            errors.append(f"{where}.path: must be a repository-relative path")
        elif isinstance(path, str):
            _credentials(errors, f"{where}.path", path)
        if line is not None and (path is None or not _positive(line)):
            errors.append(
                f"{where}.line: must be a line number, and needs a path"
            )
        if start is not None and (
            not _positive(start) or not _positive(line) or start > line
        ):
            errors.append(
                f"{where}.start_line: must be a line number no greater than"
                " line"
            )
        side = finding.get("side", "RIGHT")
        if side not in SIDES:
            errors.append(
                f"{where}.side: must be RIGHT (the changed file) or LEFT"
                " (removed lines)"
            )
        suggestion = finding.get("suggestion")
        if suggestion is not None and (
            not isinstance(suggestion, str) or line is None or side != "RIGHT"
        ):
            errors.append(
                f"{where}.suggestion: must be text replacing lines of the"
                " changed file, so it needs a line on the RIGHT side"
            )
        elif isinstance(suggestion, str):
            _credentials(errors, f"{where}.suggestion", suggestion)
        thread = finding.get("thread_url")
        if thread is not None and not (
            isinstance(thread, str) and _THREAD.fullmatch(thread)
        ):
            errors.append(
                f"{where}.thread_url: must be a review thread link ending in"
                " #discussion_rNNN"
            )
        confirmed = finding.get("confirmed_by")
        if not (
            isinstance(confirmed, list)
            and all(isinstance(c, str) for c in confirmed)
        ):
            errors.append(
                f"{where}.confirmed_by: must list the reviewers who"
                " confirmed it"
            )
        elif unknown := sorted(set(confirmed) - confirmers):
            errors.append(
                f"{where}.confirmed_by: {', '.join(unknown)} not among the"
                f" reviewers or {LEAD!r}"
            )
        elif len(set(confirmed)) != len(confirmed):
            errors.append(f"{where}.confirmed_by: lists a reviewer twice")
        elif len(confirmed) < 2:
            errors.append(
                f"{where}.confirmed_by: a finding needs two confirmations (the"
                f" reviewer who raised it and another reviewer, or {LEAD!r}"
                " after checking it against the code); drop it or confirm it"
            )

    previous = data.get("previous")
    if previous is not None:
        if not isinstance(previous, dict):
            errors.append(
                "previous: must be an object with sha, url and items"
            )
        else:
            _unknown(errors, "previous", previous, PREVIOUS_KEYS)
            if not (
                isinstance(previous.get("sha"), str)
                and _SHA.fullmatch(previous["sha"])
            ):
                errors.append(
                    "previous.sha: must be the full commit id the previous"
                    " review was made at"
                )
            url = previous.get("url")
            if url is not None and not (
                isinstance(url, str) and _REVIEW_URL.fullmatch(url)
            ):
                errors.append(
                    "previous.url: must be a link ending in"
                    " #pullrequestreview-NNN"
                )
            items = previous.get("items")
            if not isinstance(items, list):
                errors.append(
                    "previous.items: must list the previous review's findings"
                )
                items = []
            for index, item in enumerate(items):
                where = f"previous.items[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{where}: must be an object")
                    continue
                _unknown(errors, where, item, PREVIOUS_ITEM_KEYS)
                _text(
                    errors,
                    f"{where}.title",
                    item.get("title"),
                    one_line=True,
                    limit=120,
                )
                if not (
                    isinstance(item.get("status"), str)
                    and item["status"] in PREVIOUS_STATUSES
                ):
                    errors.append(
                        f"{where}.status: must be one of"
                        f" {', '.join(PREVIOUS_STATUSES)}"
                    )
                _text(
                    errors,
                    f"{where}.note",
                    item.get("note"),
                    required=False,
                    one_line=True,
                    limit=300,
                )
    try:
        json.dumps(data, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError:
        errors.append(
            "findings: contains a character that cannot be written as UTF-8 (a"
            " lone surrogate)"
        )
    return errors


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" + ("s" if word == "nit" and count != 1 else "")


def _backtick_run(text: str) -> int:
    """The length of the longest run of backticks in `text`."""
    return max((len(run) for run in re.findall(r"`+", text)), default=0)


def _fence_for(text: str) -> str:
    return "`" * max(3, _backtick_run(text) + 1)


def _indent(text: str, width: int) -> str:
    pad = " " * width
    return "\n".join(
        pad + line if line.strip() else ""
        for line in _LINE_END.split(text.strip("\n"))
    )


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _is_range(finding: dict) -> bool:
    start = finding.get("start_line")
    return bool(start) and start != finding["line"]


def _span(finding: dict) -> str:
    if _is_range(finding):
        return f"{finding['start_line']}-{finding['line']}"
    return f"{finding['line']}"


def _lines_word(finding: dict) -> tuple[str, str]:
    """('removed line', 'line'), or their plurals for a range."""
    if _is_range(finding):
        return ("removed lines", "lines")
    return ("removed line", "line")


def _code(text: str) -> str:
    """`text` as one inline code span, whatever backticks it holds.

    A file name can contain backticks.
    """
    fence = "`" * (_backtick_run(text) + 1)
    pad = " " if text[:1] in ("`", " ") or text[-1:] in ("`", " ") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _location(
    finding: dict,
    repo: str | None,
    sha: str,
    link: bool,
    notes: tuple[str, ...] = (),
) -> str:
    """`path:line`, linked to the reviewed commit when asked.

    Notes such as "inline comment" follow it.
    """
    path = finding.get("path")
    if not path:
        return f"({'; '.join(notes)})" if notes else ""
    if finding.get("line") is None:
        text = _code(path)
    else:
        text = _code(f"{path}:{_span(finding)}")
        if finding.get("side", "RIGHT") == "LEFT":
            notes = (_lines_word(finding)[0],) + notes
        elif link and repo:
            anchor = f"#L{finding['line']}"
            if _is_range(finding):
                anchor = f"#L{finding['start_line']}-L{finding['line']}"
            # ?plain=1 shows the source with line numbers even for a
            # file GitHub renders, such as Markdown.
            url = (
                f"https://github.com/{repo}/blob/{sha}/{quote(path)}"
                f"?plain=1{anchor}"
            )
            text = f"[{text}]({url})"
    return text + (f" ({'; '.join(notes)})" if notes else "")


def _anchored(finding: dict, anchors: dict) -> bool:
    lines = anchors.get(finding.get("path"), {}).get(
        finding.get("side", "RIGHT"), {}
    )
    line, start = finding.get("line"), finding.get("start_line")
    if line not in lines:
        return False
    return start is None or start == line or lines.get(start) == lines[line]


def _suggestion(text: str, label: bool) -> str:
    """`text` in a fenced block, labelled `suggestion` when asked.

    An empty suggestion block proposes deleting the lines it is on.
    """
    fence = _fence_for(text)
    body = text if not text or text.endswith("\n") else text + "\n"
    return (
        f"{fence}suggestion\n{body}{fence}"
        if label
        else f"{fence}\n{body}{fence}"
    )


def _counts(findings: list[dict]) -> dict[str, int]:
    return {
        tier: sum(1 for f in findings if f["tier"] == tier) for tier in TIERS
    }


def _method(data: dict, short: str) -> str:
    reviewers = data["reviewers"]
    angles = "; ".join(f"{r['id']} ({r['focus']})" for r in reviewers)
    if data["rounds"] == 1:
        return (
            f"{len(reviewers)} reviewers read the change at `{short}`"
            f" independently, each from one angle: {angles}. None of them"
            " found anything, so there was nothing to cross-check."
        )
    rounds = f"{data['rounds']} rounds in all"
    used_lead = any(LEAD in f["confirmed_by"] for f in data["findings"])
    agreement = (
        "Each finding above was confirmed by at least two of them, or by one"
        " of them and the agent that coordinated the review, after checking it"
        " against the code."
        if used_lead
        else "Each finding above was confirmed by at least two of them."
    )
    return (
        f"{len(reviewers)} reviewers read the change at `{short}`"
        f" independently, each from one angle: {angles}. They then checked"
        f" each other's findings ({rounds}). {agreement}"
    )


def render(
    data: dict,
    anchors: dict | None,
    *,
    version: str,
    source: str,
    event: str = "comment",
    inline: bool = True,
    footer: str | None = None,
) -> tuple[str, dict | None, list[str]]:
    """Render checked findings.

    Returns the text of review.md, the request body to post (None for a
    local review) and notes for the operator. Findings are grouped by
    tier and keep their given order within it, most important first.
    """
    repo, sha = data.get("repo"), data["head_sha"]
    short = sha[:7]
    local = data.get("pr") is None
    notes: list[str] = []
    findings = data["findings"]
    counts = _counts(findings)

    api_event = "COMMENT"
    if not local and event == "request-changes":
        if counts["blocking"]:
            api_event = "REQUEST_CHANGES"
        else:
            notes.append(
                "no blocking findings, so the review is posted as a comment,"
                " not a request for changes"
            )

    if counts["blocking"]:
        verdict = "blocking issues found"
    elif findings:
        verdict = "no blocking issues"
    else:
        verdict = "no issues found"
    header = (
        f"**Verdict: {verdict}** · {counts['blocking']} blocking ·"
        f" {counts['should-fix']} should fix · {counts['optional']} optional ·"
        f" {_plural(counts['nit'], 'nit')} · reviewed at `{short}`"
    )
    if data.get("domains"):
        header += " · domains: " + ", ".join(data["domains"])
    parts = [
        f"<!-- pr-iterative-review v{version} sha={sha} -->",
        header,
        data["summary"].strip(),
    ]
    if data.get("ci"):
        parts.append(f"**CI** at `{short}`: {data['ci']}")

    previous = data.get("previous")
    if previous:
        tally = {
            status: sum(1 for i in previous["items"] if i["status"] == status)
            for status in PREVIOUS_STATUSES
        }
        prev_short = previous["sha"][:7]
        lead = (
            f"[Previous review]({previous['url']})"
            if previous.get("url")
            else "Previous review"
        )
        section = [
            f"### Since the previous review\n\n{lead} at `{prev_short}`: "
            + " · ".join(
                f"{tally[s]} {PREVIOUS_STATUSES[s].lower()}"
                for s in PREVIOUS_STATUSES
            )
            + "."
        ]
        if previous["items"]:
            rows = ["| Earlier finding | Status | Note |", "|---|---|---|"]
            rows += [
                f"| {_cell(i['title'])} | {PREVIOUS_STATUSES[i['status']]} |"
                f" {_cell(i.get('note') or '')} |"
                for i in previous["items"]
            ]
            section.append("\n".join(rows))
        parts.append("\n\n".join(section))

    comments: list[dict] = []
    appendix: list[str] = []
    number = 0
    for tier in TIERS:
        group = [f for f in findings if f["tier"] == tier]
        if not group:
            continue
        items = []
        for finding in group:
            number += 1
            title = f"**{finding['title']}**"
            has_line = finding.get("line") is not None
            if finding.get("thread_url"):
                place = "thread"
            elif local or not inline or not has_line:
                place = "body"
            elif anchors is not None and _anchored(finding, anchors):
                place = "inline"
            else:
                place = "body"
                notes.append(
                    f"finding {number}: {finding['path']}:{_span(finding)}"
                    f" ({finding.get('side', 'RIGHT')}) is not a commentable"
                    " line of the diff, so it is in the review body"
                )
            extra = {
                "inline": ("inline comment",),
                "thread": (
                    f"still open; [thread]({finding.get('thread_url')})",
                ),
            }.get(place, ())
            location = _location(
                finding,
                repo,
                sha,
                link=place != "inline" and not local,
                notes=extra,
            )
            prefix = f"{number}. {title}" + (
                f" — {location}" if location else ""
            )
            width = len(f"{number}. ")
            if place == "inline":
                items.append(prefix)
                comment = (
                    f"**{TIER_LABELS[tier]} ({number}):"
                    f" {finding['title']}**\n\n{finding['body'].strip()}"
                )
                if finding.get("suggestion") is not None:
                    comment += "\n\n" + _suggestion(
                        finding["suggestion"], label=True
                    )
                entry = {
                    "path": finding["path"],
                    "line": finding["line"],
                    "side": finding.get("side", "RIGHT"),
                    "body": comment,
                }
                if _is_range(finding):
                    entry["start_line"] = finding["start_line"]
                    entry["start_side"] = entry["side"]
                comments.append(entry)
                where = _location(finding, repo, sha, link=False)
                appendix.append(f"### {where}\n\n{comment}")
                continue
            text = finding["body"].strip()
            if finding.get("suggestion") == "":
                text += (
                    f"\n\nSuggested change: delete {_lines_word(finding)[1]}"
                    f" {_span(finding)}."
                )
            elif finding.get("suggestion") is not None:
                text += (
                    f"\n\nSuggested replacement for {_lines_word(finding)[1]}"
                    f" {_span(finding)}:\n\n"
                    + _suggestion(finding["suggestion"], label=False)
                )
            items.append(f"{prefix}\n\n{_indent(text, width)}")
        parts.append(
            f"### {TIER_HEADINGS[tier]}\n\n"
            + "\n".join(
                item if "\n" not in item else item + "\n" for item in items
            ).rstrip("\n")
        )

    if data.get("checked"):
        parts.append(
            "### Checked and fine\n\n"
            + "\n".join(f"- {item}" for item in data["checked"])
        )
    ran = data.get("ran") or []
    not_checked = data.get("not_checked") or []
    details = [
        _method(data, short),
        "Ran:\n"
        + (
            "\n".join(f"- {item}" for item in ran)
            if ran
            else "- nothing; the code was read only"
        ),
        "Not checked:\n"
        + (
            "\n".join(f"- {item}" for item in not_checked)
            if not_checked
            else "- nothing noted"
        ),
    ]
    parts.append(
        "<details>\n<summary>How this review was made</summary>\n\n"
        + "\n\n".join(details)
        + "\n\n</details>"
    )
    if not local:
        parts.append(
            "Requesting changes for the blocking findings above; merging is"
            " for a maintainer to decide."
            if api_event == "REQUEST_CHANGES"
            else (
                "Leaving this as a comment, not an approval; merging is for a"
                " maintainer to decide."
            )
        )
    stamp = (
        f"---\n<sub>Reviewed with con/skills `pr-iterative-review` v{version}"
        f" ({source}). AI-generated: verify before acting on it.</sub>"
    )
    if footer:
        stamp += "\n\n" + footer
    parts.append(stamp)
    body = "\n\n".join(parts) + "\n"

    if len(body) > MAX_BODY:
        raise InputError(
            f"the review body is {len(body)} characters; GitHub accepts"
            f" {MAX_BODY}. Shorten the findings or move detail into inline"
            " comments"
        )
    for comment in comments:
        if len(comment["body"]) > MAX_BODY:
            raise InputError(
                f"the inline comment on {comment['path']}:{comment['line']} is"
                " too long for GitHub"
            )
    review_md = body
    if appendix:
        review_md += (
            "\n---\n\n## Inline comments\n\n" + "\n\n".join(appendix) + "\n"
        )
    payload = (
        None
        if local
        else {
            "commit_id": sha,
            "event": api_event,
            "body": body,
            "comments": comments,
        }
    )
    return review_md, payload, notes


# ----------------------------------------------------------------------
# Finding the previous review
# ----------------------------------------------------------------------


def find_previous(reviews: list, user_id: int) -> dict | None:
    """The latest review by `user_id` that carries this skill's marker.

    Pending reviews, which nobody else can see yet, do not count.
    """
    latest = None
    for review in reviews:
        if not isinstance(review, dict) or review.get("state") == "PENDING":
            continue
        if (
            not isinstance(review.get("user"), dict)
            or review["user"].get("id") != user_id
        ):
            continue
        match = _MARKER.search(review.get("body") or "")
        if not match:
            continue
        key = (str(review.get("submitted_at") or ""), review.get("id") or 0)
        if latest is None or key > latest[0]:
            latest = (key, review, match)
    if latest is None:
        return None
    _, review, match = latest
    return {
        "id": review.get("id"),
        "html_url": review.get("html_url"),
        "state": review.get("state"),
        "submitted_at": review.get("submitted_at"),
        "commit_id": review.get("commit_id"),
        "sha": match.group("sha"),
        "version": match.group("version"),
    }


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def _source(value: str) -> str:
    if not _SOURCE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "expected a commit SHA (optionally con/skills@SHA, +dirty) or "
            "'source commit unknown'; never a path or URL"
        )
    return value


def _sha(value: str) -> str:
    if not _SHA.fullmatch(value):
        raise argparse.ArgumentTypeError(
            f"expected a 40-character commit id, got {value!r}"
        )
    return value


def cmd_render(args: argparse.Namespace) -> int:
    data = load_json(args.findings)
    errors = check_findings(data)
    if args.footer is not None:
        _text(errors, "--footer", args.footer, one_line=True, limit=300)
    if errors:
        raise InputError(
            "the findings cannot be rendered:\n  " + "\n  ".join(errors)
        )
    anchors = None
    if data.get("pr") is not None:
        if not args.diff:
            raise InputError(
                "--diff is required for a pull request: inline comments are"
                " checked against it"
            )
        # Only the diff's structure matters here, so text in another
        # encoding is harmless. Read bytes: decoding a text file would
        # also turn a carriage return inside a changed line into a
        # newline.
        anchors = parse_diff(
            Path(args.diff).read_bytes().decode("utf-8", errors="replace")
        )
    skill_dir = Path(__file__).resolve().parent.parent
    review_md, payload, notes = render(
        data,
        anchors,
        version=skill_version(skill_dir),
        source=args.source,
        event=args.event,
        inline=not args.no_inline,
        footer=args.footer,
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "review.md").write_text(review_md, encoding="utf-8")
    written = [str(out / "review.md")]
    if payload is not None:
        (out / "payload.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(str(out / "payload.json"))
    for note in notes:
        print(f"note: {note}", file=sys.stderr)
    tiers = ", ".join(
        f"{count} {tier}" for tier, count in _counts(data["findings"]).items()
    )
    inline = len(payload["comments"]) if payload else 0
    print(
        f"{len(data['findings'])} findings ({tiers}); {inline} inline; wrote"
        f" {' and '.join(written)}"
    )
    return 0


def cmd_previous(args: argparse.Namespace) -> int:
    found = find_previous(pages(load_json(args.reviews)), args.user_id)
    if found is not None and args.head_sha:
        found["already_reviewed"] = found["sha"] == args.head_sha
    print(json.dumps(found, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_cmd = subparsers.add_parser(
        "render", help="render findings into review.md and payload.json"
    )
    render_cmd.add_argument("findings", help="the reconciled findings (JSON)")
    render_cmd.add_argument(
        "--out",
        required=True,
        help="directory to write review.md and payload.json into",
    )
    render_cmd.add_argument(
        "--diff", help="the pull request diff the review will be posted on"
    )
    render_cmd.add_argument(
        "--event",
        choices=EVENTS,
        default="comment",
        help=(
            "request-changes only when the invocation asked for it; never an"
            " approval"
        ),
    )
    render_cmd.add_argument(
        "--no-inline",
        action="store_true",
        help=(
            "put every finding in the review body (after GitHub refused an"
            " inline comment)"
        ),
    )
    render_cmd.add_argument(
        "--source",
        type=_source,
        default="source commit unknown",
        help=(
            "the con/skills commit this skill was installed from, for the"
            " stamp"
        ),
    )
    render_cmd.add_argument(
        "--footer", help="one line the host requires on everything it posts"
    )
    previous_cmd = subparsers.add_parser(
        "previous", help="find this skill's latest review by one account"
    )
    previous_cmd.add_argument(
        "reviews",
        help="JSON from GET /repos/O/R/pulls/N/reviews, every page (--slurp)",
    )
    previous_cmd.add_argument(
        "--user-id",
        required=True,
        type=int,
        help="account id the reviews were posted from",
    )
    previous_cmd.add_argument(
        "--head-sha", type=_sha, help="the pull request's current head commit"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"render": cmd_render, "previous": cmd_previous}
    try:
        return handlers[args.command](args)
    except (InputError, OSError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
