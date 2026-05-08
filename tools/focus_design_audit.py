#!/usr/bin/env python3
"""Audit focus-created equipment variants across base, Sheep, and DAI.

This is intentionally a lightweight Clausewitz-script scanner rather than a
full parser. It tracks nested blocks well enough to find focus blocks and their
create_equipment_variant effects, then emits a human-readable markdown report.
"""

from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


BLOCK_KEY_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@.:-[]?")
ASSIGN_RE = re.compile(
    r"^\s*([A-Za-z0-9_@.\-:\[\]\?]+)\s*=\s*(\"[^\"]*\"|[^\s{}#]+)",
    re.MULTILINE,
)
AI_GATE_RE = re.compile(r"\bis_ai\s*=\s*(yes|no)\b")
DLC_RE = re.compile(r"\bhas_dlc\s*=\s*(\"[^\"]+\"|[^\s{}#]+)")


@dataclass
class Node:
    key: str
    key_start: int
    body_start: int
    parent: "Node | None" = None
    end: int | None = None
    children: list["Node"] = field(default_factory=list)

    @property
    def start(self) -> int:
        return self.key_start

    def ancestors(self) -> Iterable["Node"]:
        node = self.parent
        while node is not None:
            yield node
            node = node.parent


@dataclass
class VariantEntry:
    repo: str
    rel_path: str
    line: int
    focus_id: str
    focus_kind: str
    index_in_focus: int
    name: str
    type: str
    design_team: str
    ai_gate: str
    dlc_gate: str
    flags: str
    modules: str
    upgrades: str
    signature: str

    @property
    def key(self) -> tuple[str, str, int]:
        return (self.rel_path, self.focus_id, self.index_in_focus)


def strip_comments_preserve(text: str) -> str:
    out: list[str] = []
    in_quote = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"':
            in_quote = not in_quote
            out.append(ch)
        elif ch == "#" and not in_quote:
            while i < len(text) and text[i] != "\n":
                out.append(" ")
                i += 1
            if i < len(text):
                out.append("\n")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def line_starts(text: str) -> list[int]:
    starts = [0]
    starts.extend(match.end() for match in re.finditer(r"\n", text))
    return starts


def line_for_pos(starts: list[int], pos: int) -> int:
    return bisect.bisect_right(starts, pos)


def block_key_before(text: str, brace_pos: int) -> tuple[str, int] | None:
    i = brace_pos - 1
    while i >= 0 and text[i].isspace():
        i -= 1
    if i < 0 or text[i] != "=":
        return None
    i -= 1
    while i >= 0 and text[i].isspace():
        i -= 1
    end = i + 1
    while i >= 0 and text[i] in BLOCK_KEY_CHARS:
        i -= 1
    start = i + 1
    if start == end:
        return None
    return text[start:end], start


def parse_blocks(clean_text: str) -> Node:
    root = Node("<root>", 0, 0, None)
    stack = [root]
    i = 0
    while i < len(clean_text):
        ch = clean_text[i]
        if ch == "{":
            key = block_key_before(clean_text, i)
            if key is not None:
                node = Node(key[0], key[1], i, stack[-1])
                stack[-1].children.append(node)
                stack.append(node)
        elif ch == "}":
            if len(stack) > 1:
                stack[-1].end = i
                stack.pop()
        i += 1
    for node in stack[1:]:
        node.end = len(clean_text)
    root.end = len(clean_text)
    return root


def walk(node: Node) -> Iterable[Node]:
    for child in node.children:
        yield child
        yield from walk(child)


def masked_body(text: str, node: Node) -> str:
    end = node.end if node.end is not None else len(text)
    start = node.body_start + 1
    chars = list(text[start:end])
    for child in node.children:
        child_start = max(child.key_start - start, 0)
        child_end = min((child.end if child.end is not None else end) - start + 1, len(chars))
        for i in range(child_start, child_end):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def direct_assignments(text: str, node: Node) -> dict[str, str]:
    body = masked_body(text, node)
    result: dict[str, str] = {}
    for key, value in ASSIGN_RE.findall(body):
        result[key] = value.strip('"')
    return result


def child_blocks(node: Node, key: str) -> list[Node]:
    return [child for child in node.children if child.key == key]


def summarize_assignment_block(text: str, node: Node | None) -> str:
    if node is None:
        return ""
    assignments = direct_assignments(text, node)
    if assignments:
        return "; ".join(f"{key}={value}" for key, value in assignments.items())
    end = node.end if node.end is not None else len(text)
    raw = re.sub(r"\s+", " ", text[node.body_start + 1 : end]).strip()
    return raw[:220] + ("..." if len(raw) > 220 else "")


def nearest_focus(node: Node) -> Node | None:
    for ancestor in node.ancestors():
        if ancestor.key in {"focus", "shared_focus"}:
            return ancestor
    return None


def find_context_patterns(text: str, variant: Node, focus: Node | None) -> tuple[str, str]:
    search_ranges: list[tuple[int, int, str]] = []
    for ancestor in variant.ancestors():
        if ancestor.key in {"if", "else_if", "else", "available", "complete_effect", "select_effect"}:
            search_ranges.append((ancestor.body_start, variant.start, ancestor.key))
        if focus is not None and ancestor is focus:
            break

    ai_gate = ""
    dlcs: list[str] = []
    for start, end, label in search_ranges:
        if start >= end:
            continue
        snippet = text[start:end]
        if not ai_gate:
            match = AI_GATE_RE.search(snippet)
            if match:
                ai_gate = f"is_ai={match.group(1)} in enclosing {label}"
        for match in DLC_RE.finditer(snippet):
            value = match.group(1).strip('"')
            if value not in dlcs:
                dlcs.append(value)

    return ai_gate or "none found", ", ".join(dlcs)


def collect_entries(repo: str, root: Path) -> list[VariantEntry]:
    focus_dir = root / "common" / "national_focus"
    if not focus_dir.exists():
        return []

    entries: list[VariantEntry] = []
    counters: dict[tuple[str, str], int] = {}
    for path in sorted(focus_dir.rglob("*.txt")):
        rel_path = path.relative_to(root).as_posix()
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        clean = strip_comments_preserve(raw)
        starts = line_starts(raw)
        tree = parse_blocks(clean)
        for node in walk(tree):
            if node.key != "create_equipment_variant":
                continue
            focus = nearest_focus(node)
            if focus is None:
                focus_id = "<outside focus>"
                focus_kind = "<unknown>"
            else:
                focus_assignments = direct_assignments(clean, focus)
                focus_id = focus_assignments.get("id", "<missing id>")
                focus_kind = focus.key

            counter_key = (rel_path, focus_id)
            counters[counter_key] = counters.get(counter_key, 0) + 1
            index = counters[counter_key]

            assignments = direct_assignments(clean, node)
            modules = summarize_assignment_block(clean, child_blocks(node, "modules")[0] if child_blocks(node, "modules") else None)
            upgrades = summarize_assignment_block(clean, child_blocks(node, "upgrades")[0] if child_blocks(node, "upgrades") else None)
            flags = []
            for flag in (
                "obsolete",
                "mark_older_equipment_obsolete",
                "allow_without_tech",
                "parent_version",
            ):
                if flag in assignments:
                    flags.append(f"{flag}={assignments[flag]}")
            ai_gate, dlc_gate = find_context_patterns(clean, node, focus)
            name = assignments.get("name", assignments.get("name_group", "<unnamed>"))
            eq_type = assignments.get("type", "<missing type>")
            design_team = assignments.get("design_team", "")
            signature = "|".join(
                [
                    name,
                    eq_type,
                    design_team,
                    ";".join(flags),
                    modules,
                    upgrades,
                ]
            )
            entries.append(
                VariantEntry(
                    repo=repo,
                    rel_path=rel_path,
                    line=line_for_pos(starts, node.start),
                    focus_id=focus_id,
                    focus_kind=focus_kind,
                    index_in_focus=index,
                    name=name,
                    type=eq_type,
                    design_team=design_team,
                    ai_gate=ai_gate,
                    dlc_gate=dlc_gate,
                    flags=", ".join(flags),
                    modules=modules,
                    upgrades=upgrades,
                    signature=signature,
                )
            )
    return entries


def type_group(eq_type: str) -> str:
    lowered = eq_type.lower()
    if "airframe" in lowered or "plane" in lowered or "fighter" in lowered or "cas" in lowered:
        return "air"
    if "ship" in lowered or "submarine" in lowered or "carrier" in lowered:
        return "navy"
    if "tank" in lowered or "armor" in lowered:
        return "armor"
    return "other"


def compact_variant(entry: VariantEntry | None) -> str:
    if entry is None:
        return "-"
    parts = [f"L{entry.line}", entry.name, entry.type]
    engine = ""
    for piece in entry.modules.split("; "):
        if piece.startswith("engine_type_slot="):
            engine = piece.removeprefix("engine_type_slot=")
            break
    if engine:
        parts.append(f"engine={engine}")
    if entry.flags:
        parts.append(entry.flags)
    return "<br>".join(escape_md(part) for part in parts)


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def changed(a: VariantEntry | None, b: VariantEntry | None) -> bool:
    return a is not None and b is not None and a.signature != b.signature


def blocks_ai(entry: VariantEntry | None) -> bool:
    return entry is not None and "is_ai=no" in entry.ai_gate


def status_note(base: VariantEntry | None, sheep: VariantEntry | None, dai: VariantEntry | None) -> str:
    notes: list[str] = []
    if dai is not None:
        notes.append("DAI override present")
        if base is not None and changed(base, dai):
            notes.append("DAI differs from base")
        if blocks_ai(dai):
            notes.append("DAI blocks AI")
        elif blocks_ai(sheep):
            notes.append("DAI lacks Sheep AI block")
    elif base is not None:
        notes.append("DAI inherits base")
    else:
        notes.append("not in base/DAI")

    if sheep is not None:
        if base is None:
            notes.append("Sheep-only reference")
        elif changed(base, sheep):
            notes.append("Sheep differs from base")
        else:
            notes.append("Sheep same as base")
        if "is_ai=no" in sheep.ai_gate:
            notes.append("Sheep blocks AI")
    elif base is not None:
        notes.append("not covered by Sheep file")
    return "; ".join(notes)


def focus_overview(entries_by_repo: dict[str, list[VariantEntry]]) -> list[tuple[str, str, dict[str, int]]]:
    counts: dict[tuple[str, str], dict[str, int]] = {}
    for repo, entries in entries_by_repo.items():
        for entry in entries:
            key = (entry.rel_path, entry.focus_id)
            counts.setdefault(key, {})
            counts[key][repo] = counts[key].get(repo, 0) + 1
    return [(path, focus, repo_counts) for (path, focus), repo_counts in sorted(counts.items())]


def build_report(base: Path, sheep: Path, dai: Path) -> str:
    repos = {
        "base": collect_entries("base", base),
        "sheep": collect_entries("sheep", sheep),
        "dai": collect_entries("dai", dai),
    }
    by_repo_key = {
        repo: {entry.key: entry for entry in entries}
        for repo, entries in repos.items()
    }
    all_keys = sorted(set().union(*(set(entries.keys()) for entries in by_repo_key.values())))
    sheep_keys = set(by_repo_key["sheep"].keys())

    lines: list[str] = []
    today = _dt.date.today().isoformat()
    lines.append("# Focus-Created Equipment Variant Audit")
    lines.append("")
    lines.append(f"Generated: {today}")
    lines.append("")
    lines.append("Scope: `common/national_focus/**/*.txt` in vanilla/base, Sheep's AI reference, and Dynamic AI MP.")
    lines.append("This report treats each `create_equipment_variant` effect as one design entry and groups entries by focus id plus occurrence order inside that focus.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Source | Variant effects | Focuses | Files |")
    lines.append("| --- | ---: | ---: | ---: |")
    for repo, entries in repos.items():
        focuses = {(entry.rel_path, entry.focus_id) for entry in entries}
        files = {entry.rel_path for entry in entries}
        lines.append(f"| {repo} | {len(entries)} | {len(focuses)} | {len(files)} |")
    lines.append("")
    lines.append("## Reading Notes")
    lines.append("")
    lines.append("- `DAI inherits base` means this mod does not override that same focus-created design entry, so vanilla behavior is the active fallback.")
    lines.append("- `Sheep blocks AI` means Sheep has an enclosing `is_ai = no` gate near the variant creation effect.")
    lines.append("- Entries are matched by `file + focus id + occurrence number`; if a focus adds/removes variants between repos, verify that focus manually before copying changes.")
    lines.append("- Module summaries call out engines inline when present; full module assignments are in the detailed Sheep section.")
    lines.append("")

    lines.append("## Focus Overview")
    lines.append("")
    lines.append("| File | Focus | Base | Sheep | DAI |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for path, focus, counts in focus_overview(repos):
        lines.append(
            f"| `{escape_md(path)}` | `{escape_md(focus)}` | {counts.get('base', 0)} | {counts.get('sheep', 0)} | {counts.get('dai', 0)} |"
        )
    lines.append("")

    lines.append("## Likely DAI Follow-Up Candidates")
    lines.append("")
    lines.append("These are Sheep reference entries where Sheep differs from base or blocks the AI, while DAI either does not override the same entry or does not carry Sheep's gate/signature.")
    lines.append("")
    lines.append("| File | Focus | # | Category | Sheep | Base | DAI | Note |")
    lines.append("| --- | --- | ---: | --- | --- | --- | --- | --- |")
    candidate_count = 0
    for key in sorted(sheep_keys):
        sheep_entry = by_repo_key["sheep"].get(key)
        base_entry = by_repo_key["base"].get(key)
        dai_entry = by_repo_key["dai"].get(key)
        if sheep_entry is None:
            continue
        sheep_has_notable_change = base_entry is None or changed(base_entry, sheep_entry) or blocks_ai(sheep_entry)
        dai_needs_attention = (
            dai_entry is None
            or changed(dai_entry, sheep_entry)
            or (blocks_ai(sheep_entry) and not blocks_ai(dai_entry))
        )
        if sheep_has_notable_change and dai_needs_attention:
            candidate_count += 1
            lines.append(
                "| `{}` | `{}` | {} | {} | {} | {} | {} | {} |".format(
                    escape_md(key[0]),
                    escape_md(key[1]),
                    key[2],
                    type_group(sheep_entry.type),
                    compact_variant(sheep_entry),
                    compact_variant(base_entry),
                    compact_variant(dai_entry),
                    escape_md(status_note(base_entry, sheep_entry, dai_entry)),
                )
            )
    if candidate_count == 0:
        lines.append("| - | - | - | - | - | - | No candidates found. |")
    lines.append("")

    lines.append("## Exhaustive Variant Comparison")
    lines.append("")
    lines.append("| File | Focus | # | Base | Sheep | DAI | Status |")
    lines.append("| --- | --- | ---: | --- | --- | --- | --- |")
    for key in all_keys:
        base_entry = by_repo_key["base"].get(key)
        sheep_entry = by_repo_key["sheep"].get(key)
        dai_entry = by_repo_key["dai"].get(key)
        lines.append(
            "| `{}` | `{}` | {} | {} | {} | {} | {} |".format(
                escape_md(key[0]),
                escape_md(key[1]),
                key[2],
                compact_variant(base_entry),
                compact_variant(sheep_entry),
                compact_variant(dai_entry),
                escape_md(status_note(base_entry, sheep_entry, dai_entry)),
            )
        )
    lines.append("")

    lines.append("## Sheep Detailed Reference")
    lines.append("")
    lines.append("Use this when copying Sheep-style focus changes. It preserves the nearby AI/DLC gate signal and the module/upgrades summary from Sheep.")
    lines.append("")
    current_group: tuple[str, str] | None = None
    for entry in sorted(repos["sheep"], key=lambda item: (item.rel_path, item.focus_id, item.index_in_focus)):
        group = (entry.rel_path, entry.focus_id)
        if group != current_group:
            current_group = group
            lines.append(f"### `{escape_md(entry.rel_path)}` - `{escape_md(entry.focus_id)}`")
            lines.append("")
        lines.append(f"- #{entry.index_in_focus} L{entry.line}: `{escape_md(entry.name)}` / `{escape_md(entry.type)}`")
        if entry.design_team:
            lines.append(f"  - design team: `{escape_md(entry.design_team)}`")
        lines.append(f"  - AI gate: {escape_md(entry.ai_gate)}")
        if entry.dlc_gate:
            lines.append(f"  - DLC gate: {escape_md(entry.dlc_gate)}")
        if entry.flags:
            lines.append(f"  - flags: `{escape_md(entry.flags)}`")
        if entry.modules:
            lines.append(f"  - modules: `{escape_md(entry.modules)}`")
        if entry.upgrades:
            lines.append(f"  - upgrades: `{escape_md(entry.upgrades)}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("../hoi4-ai-base"))
    parser.add_argument("--sheep", type=Path, default=Path("../sheep-ai-mod"))
    parser.add_argument("--dai", type=Path, default=Path("."))
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()

    report = build_report(args.base.resolve(), args.sheep.resolve(), args.dai.resolve())
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(report, encoding="utf-8", newline="\n")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
