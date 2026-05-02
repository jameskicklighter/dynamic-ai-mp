#!/usr/bin/env python3
"""
Patch audit helper for Dynamic AI MP.

This script is meant for agents working on Hearts of Iron IV patch merges. It
does not edit files. It produces a report that answers two separate questions:

1. Patch overlap: which base-game files changed between two refs, which of
   those files are overwritten by the mod, and which newly added upstream
   objects are missing from the mod.
2. Drift scan: for long-lived overwritten data files, which current-base
   objects are missing from the mod even if the latest patch did not touch that
   file.

Typical use from the mod repo:

    python tools/patch_audit.py --base-repo ../hoi4-ai-base --old-ref HEAD~1 --new-ref HEAD

Write a reusable report:

    python tools/patch_audit.py --base-repo ../hoi4-ai-base --old-ref bcb9299 --new-ref 6b60da5 --write reports/patch-audit-1.18.1.md

The report is a starting point for the A/B/C merge rule in
`agent-guidance/patch-merge.instructions.md`; it is not a substitute for
judgment. AI tuning helper dirs are skipped by default because this mod
intentionally owns most AI weights. `common/ai_strategy` is still reviewed by
default, but strategy results are review notes unless the user explicitly asks
for those changes.
"""

from __future__ import annotations

import argparse
import bisect
import datetime as _dt
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


AI_TUNING_DIRS = (
    "common/ai_equipment/",
    "common/ai_focuses/",
    "common/ai_strategy_plans/",
    "common/ai_templates/",
)

AI_STRATEGY_DIRS = (
    "common/ai_strategy/",
)

HIGH_VALUE_DIRS = (
    "common/abilities/",
    "common/characters/",
    "common/continuous_focus/",
    "common/country_leader/",
    "common/decisions/",
    "common/defines/",
    "common/doctrines/",
    "common/factions/",
    "common/ideas/",
    "common/national_focus/",
    "common/on_actions/",
    "common/scripted_effects/",
    "common/scripted_triggers/",
    "common/technologies/",
    "events/",
)

BLOCK_COMPARE_IGNORE_KEYS = {
    "ai_will_do",
}

GENERIC_CONTAINER_KEYS = {
    "allowed",
    "available",
    "bypass",
    "cancel_trigger",
    "categories",
    "complete_effect",
    "completion_reward",
    "cost",
    "custom_cost_trigger",
    "equipment_bonus",
    "folder",
    "limit",
    "modifier",
    "mutually_exclusive",
    "prerequisite",
    "remove_effect",
    "targeted_modifier",
    "visible",
}

DECISION_CATEGORY_ATTR_KEYS = {
    "allowed",
    "available",
    "cancel_trigger",
    "custom_cost_text",
    "custom_cost_trigger",
    "highlight_states",
    "icon",
    "modifier",
    "picture",
    "remove_effect",
    "state_target",
    "target_array",
    "target_trigger",
    "visible",
}

EVENT_BLOCK_KEYS = {
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
}


@dataclass
class ChangedFile:
    status: str
    path: str
    old_path: Optional[str] = None


@dataclass
class Block:
    key: str
    key_start: int
    open_brace: int
    start_line: int
    parent: Optional[int]
    children: List[int] = field(default_factory=list)
    end: Optional[int] = None
    end_line: Optional[int] = None


@dataclass
class ObjectEntry:
    kind: str
    label: str
    display: str
    line: int
    raw: str
    order_index: int


@dataclass
class ObjectSet:
    entries: List[ObjectEntry]
    by_key: Dict[str, ObjectEntry]
    diagnostics: List[str]


@dataclass
class FileAudit:
    path: str
    missing_new: List[ObjectEntry] = field(default_factory=list)
    present_new: List[ObjectEntry] = field(default_factory=list)
    changed_existing_review: List[ObjectEntry] = field(default_factory=list)
    changed_existing_absent: List[ObjectEntry] = field(default_factory=list)
    changed_existing_matching: List[ObjectEntry] = field(default_factory=list)
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class DriftAudit:
    path: str
    missing_current: List[ObjectEntry] = field(default_factory=list)
    mod_only_count: int = 0
    order_mismatch: Optional[str] = None
    diagnostics: List[str] = field(default_factory=list)


def run_git(base_repo: Path, args: Sequence[str], allow_error: bool = False) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", "-C", str(base_repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode and not allow_error:
        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"git {' '.join(args)} failed: {stderr}")
    return proc


def git_text(base_repo: Path, ref: str, rel_path: str) -> Optional[str]:
    proc = run_git(base_repo, ["show", f"{ref}:{rel_path}"], allow_error=True)
    if proc.returncode:
        return None
    return proc.stdout.decode("utf-8-sig", errors="replace")


def changed_files(base_repo: Path, old_ref: str, new_ref: str) -> List[ChangedFile]:
    proc = run_git(base_repo, ["diff", "--name-status", old_ref, new_ref, "--"])
    out = proc.stdout.decode("utf-8", errors="replace")
    changed: List[ChangedFile] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            changed.append(ChangedFile(status=status, path=norm_path(parts[2]), old_path=norm_path(parts[1])))
        elif len(parts) >= 2:
            changed.append(ChangedFile(status=status, path=norm_path(parts[1])))
    return changed


def norm_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def lower_path(path: str) -> str:
    return norm_path(path).lower()


def is_ai_tuning_path(path: str) -> bool:
    p = lower_path(path)
    return any(p.startswith(prefix) for prefix in AI_TUNING_DIRS)


def is_ai_strategy_path(path: str) -> bool:
    p = lower_path(path)
    return any(p.startswith(prefix) for prefix in AI_STRATEGY_DIRS)


def is_high_value_path(path: str) -> bool:
    p = lower_path(path)
    return any(p.startswith(prefix) for prefix in HIGH_VALUE_DIRS)


def is_mod_specific_path(path: str) -> bool:
    parts = norm_path(path).split("/")
    return any(part.upper().startswith("DAI_") for part in parts)


def mod_file_path(mod_root: Path, rel_path: str) -> Path:
    return mod_root.joinpath(*norm_path(rel_path).split("/"))


def read_mod_text(mod_root: Path, rel_path: str) -> Optional[str]:
    path = mod_file_path(mod_root, rel_path)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8-sig", errors="replace")


def line_starts(text: str) -> List[int]:
    starts = [0]
    for match in re.finditer(r"\n", text):
        starts.append(match.end())
    return starts


def line_no(starts: Sequence[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


def mask_comments_and_strings(text: str) -> str:
    chars = list(text)
    in_string = False
    i = 0
    while i < len(chars):
        ch = chars[i]
        if in_string:
            if ch == '"':
                in_string = False
            if ch not in "\r\n":
                chars[i] = " "
            i += 1
            continue
        if ch == '"':
            in_string = True
            chars[i] = " "
            i += 1
            continue
        if ch == "#":
            while i < len(chars) and chars[i] not in "\r\n":
                chars[i] = " "
                i += 1
            continue
        i += 1
    return "".join(chars)


def parse_blocks(text: str) -> Tuple[List[Block], List[str]]:
    clean = mask_comments_and_strings(text)
    starts = line_starts(text)
    key_pattern = re.compile(r"([A-Za-z0-9_@.:\-/]+)\s*=\s*$")
    blocks: List[Block] = []
    stack: List[Optional[int]] = []
    diagnostics: List[str] = []

    for match in re.finditer(r"[{}]", clean):
        token = match.group(0)
        if token == "{":
            prefix_start = max(0, match.start() - 256)
            prefix = clean[prefix_start:match.start()]
            key_match = key_pattern.search(prefix)
            if key_match is None:
                stack.append(None)
                continue
            key = key_match.group(1)
            key_start = prefix_start + key_match.start(1)
            parent = next((item for item in reversed(stack) if item is not None), None)
            block = Block(
                key=key,
                key_start=key_start,
                open_brace=match.start(),
                start_line=line_no(starts, key_start),
                parent=parent,
            )
            index = len(blocks)
            blocks.append(block)
            if parent is not None:
                blocks[parent].children.append(index)
            stack.append(index)
        elif not stack:
            diagnostics.append(f"unmatched closing brace at line {line_no(starts, match.start())}")
        else:
            index = stack.pop()
            if index is not None:
                blocks[index].end = match.end()
                blocks[index].end_line = line_no(starts, match.start())

    for index in stack:
        if index is not None:
            block = blocks[index]
            diagnostics.append(f"unclosed block '{block.key}' starting at line {block.start_line}")
        else:
            diagnostics.append("unclosed anonymous brace block")
    return blocks, diagnostics


def block_raw(text: str, block: Block) -> str:
    end = block.end if block.end is not None else len(text)
    return text[block.key_start:end]


def root_blocks(blocks: Sequence[Block]) -> List[int]:
    return [i for i, block in enumerate(blocks) if block.parent is None]


def first_wrapper(blocks: Sequence[Block], key: str) -> Optional[int]:
    for index, block in enumerate(blocks):
        if block.key == key:
            return index
    return None


def direct_assignment(raw: str, key: str) -> Optional[str]:
    masked = mask_comments_and_strings(raw)
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*\"?([^\"\s{{}}#]+)\"?", masked)
    if match:
        return match.group(1)
    return None


def append_child_entries(
    entries: List[ObjectEntry],
    text: str,
    blocks: Sequence[Block],
    parent_index: int,
    kind: str,
    prefix: str = "",
    exclude: Iterable[str] = (),
) -> None:
    excluded = set(exclude)
    for child_index in blocks[parent_index].children:
        child = blocks[child_index]
        if child.key in excluded:
            continue
        label = f"{prefix}{child.key}"
        entries.append(ObjectEntry(kind, label, f"{kind}:{label}", child.start_line, block_raw(text, child), len(entries)))


def extract_focus_objects(path: str, text: str, blocks: Sequence[Block]) -> List[ObjectEntry]:
    entries: List[ObjectEntry] = []
    for block in blocks:
        if block.key != "focus":
            continue
        raw = block_raw(text, block)
        ident = direct_assignment(raw, "id")
        if ident:
            entries.append(ObjectEntry("focus", ident, f"focus:{ident}", block.start_line, raw, len(entries)))

    masked = mask_comments_and_strings(text)
    for match in re.finditer(r"(?m)^\s*shared_focus\s*=\s*\"?([^\"\s{}#]+)\"?", masked):
        ident = match.group(1)
        starts = line_starts(text)
        entries.append(ObjectEntry("shared_focus", ident, f"shared_focus:{ident}", line_no(starts, match.start()), match.group(0), len(entries)))
    return entries


def extract_event_objects(text: str, blocks: Sequence[Block]) -> List[ObjectEntry]:
    entries: List[ObjectEntry] = []
    for block in blocks:
        if block.key not in EVENT_BLOCK_KEYS:
            continue
        raw = block_raw(text, block)
        ident = direct_assignment(raw, "id")
        if ident:
            entries.append(ObjectEntry(block.key, ident, f"{block.key}:{ident}", block.start_line, raw, len(entries)))
    return entries


def extract_lua_defines(text: str) -> List[ObjectEntry]:
    entries: List[ObjectEntry] = []
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.split("--", 1)[0].strip()
        match = re.match(r"(NDefines\.[A-Za-z0-9_.]+)\s*=", stripped)
        if match:
            ident = match.group(1)
            entries.append(ObjectEntry("define", ident, f"define:{ident}", index, line, len(entries)))
    return entries


def extract_objects(rel_path: str, text: Optional[str]) -> ObjectSet:
    if text is None:
        return ObjectSet([], {}, ["file is absent"])

    path = lower_path(rel_path)
    if path.endswith(".lua") or path.startswith("common/defines/"):
        entries = extract_lua_defines(text)
        return ObjectSet(entries, unique_entries(entries), [])

    blocks, diagnostics = parse_blocks(text)
    entries: List[ObjectEntry] = []

    if path.startswith("common/country_leader/"):
        wrapper = first_wrapper(blocks, "leader_traits")
        if wrapper is not None:
            append_child_entries(entries, text, blocks, wrapper, "trait")
    elif path.startswith("common/characters/"):
        wrapper = first_wrapper(blocks, "characters")
        if wrapper is not None:
            append_child_entries(entries, text, blocks, wrapper, "character")
    elif path.startswith("common/technologies/"):
        wrapper = first_wrapper(blocks, "technologies")
        if wrapper is not None:
            append_child_entries(entries, text, blocks, wrapper, "technology", exclude={"folders"})
    elif path.startswith("common/ideas/"):
        wrapper = first_wrapper(blocks, "ideas")
        if wrapper is not None:
            for category_index in blocks[wrapper].children:
                category = blocks[category_index]
                entries.append(ObjectEntry("idea_category", category.key, f"idea_category:{category.key}", category.start_line, block_raw(text, category), len(entries)))
                for child_index in category.children:
                    child = blocks[child_index]
                    label = f"{category.key}/{child.key}"
                    entries.append(ObjectEntry("idea", label, f"idea:{label}", child.start_line, block_raw(text, child), len(entries)))
    elif path.startswith("common/decisions/"):
        for category_index in root_blocks(blocks):
            category = blocks[category_index]
            entries.append(ObjectEntry("decision_category", category.key, f"decision_category:{category.key}", category.start_line, block_raw(text, category), len(entries)))
            for child_index in category.children:
                child = blocks[child_index]
                if child.key in DECISION_CATEGORY_ATTR_KEYS:
                    continue
                label = f"{category.key}/{child.key}"
                entries.append(ObjectEntry("decision", label, f"decision:{label}", child.start_line, block_raw(text, child), len(entries)))
    elif path.startswith("common/national_focus/"):
        entries.extend(extract_focus_objects(rel_path, text, blocks))
    elif path.startswith("events/"):
        entries.extend(extract_event_objects(text, blocks))
    elif path.startswith("common/scripted_effects/"):
        for index in root_blocks(blocks):
            block = blocks[index]
            entries.append(ObjectEntry("scripted_effect", block.key, f"scripted_effect:{block.key}", block.start_line, block_raw(text, block), len(entries)))
    elif path.startswith("common/scripted_triggers/"):
        for index in root_blocks(blocks):
            block = blocks[index]
            entries.append(ObjectEntry("scripted_trigger", block.key, f"scripted_trigger:{block.key}", block.start_line, block_raw(text, block), len(entries)))
    elif path.startswith("common/on_actions/"):
        for index in root_blocks(blocks):
            block = blocks[index]
            entries.append(ObjectEntry("on_action", block.key, f"on_action:{block.key}", block.start_line, block_raw(text, block), len(entries)))
    else:
        for index in root_blocks(blocks):
            block = blocks[index]
            if block.key in GENERIC_CONTAINER_KEYS:
                continue
            entries.append(ObjectEntry("object", block.key, f"object:{block.key}", block.start_line, block_raw(text, block), len(entries)))

    return ObjectSet(entries, unique_entries(entries), diagnostics)


def unique_entries(entries: Sequence[ObjectEntry]) -> Dict[str, ObjectEntry]:
    base_keys = [f"{entry.kind}:{entry.label}" for entry in entries]
    totals = Counter(base_keys)
    seen: Dict[str, int] = defaultdict(int)
    out: Dict[str, ObjectEntry] = {}
    for entry, base_key in zip(entries, base_keys):
        seen[base_key] += 1
        if totals[base_key] == 1:
            key = base_key
            display = entry.display
        else:
            key = f"{base_key}#{seen[base_key]}"
            display = f"{entry.display} [{seen[base_key]}]"
        out[key] = ObjectEntry(entry.kind, entry.label, display, entry.line, entry.raw, entry.order_index)
    return out


def remove_ignored_blocks(raw: str, ignore_keys: Iterable[str]) -> str:
    ignored = set(ignore_keys)
    blocks, _ = parse_blocks(raw)
    ranges: List[Tuple[int, int]] = []
    for block in blocks:
        if block.key in ignored and block.end is not None:
            ranges.append((block.key_start, block.end))
    if not ranges:
        return raw
    pieces: List[str] = []
    cursor = 0
    for start, end in sorted(ranges):
        if start < cursor:
            continue
        pieces.append(raw[cursor:start])
        cursor = end
    pieces.append(raw[cursor:])
    return "".join(pieces)


def normalize_for_compare(raw: str, ignore_ai: bool) -> str:
    if ignore_ai:
        raw = remove_ignored_blocks(raw, BLOCK_COMPARE_IGNORE_KEYS)
    without_comments = mask_comments_and_strings(raw)
    return re.sub(r"\s+", "", without_comments)


def analyze_patch_file(
    rel_path: str,
    old_text: Optional[str],
    new_text: Optional[str],
    mod_text: Optional[str],
    ignore_ai: bool,
) -> FileAudit:
    audit = FileAudit(path=rel_path)
    old_objects = extract_objects(rel_path, old_text)
    new_objects = extract_objects(rel_path, new_text)
    mod_objects = extract_objects(rel_path, mod_text)

    for source_name, object_set in (("old base", old_objects), ("new base", new_objects), ("mod", mod_objects)):
        for diagnostic in object_set.diagnostics:
            audit.diagnostics.append(f"{source_name}: {diagnostic}")

    old_keys = set(old_objects.by_key)
    new_keys = set(new_objects.by_key)
    mod_keys = set(mod_objects.by_key)

    for key in sorted(new_keys - old_keys, key=lambda item: new_objects.by_key[item].order_index):
        if key in mod_keys:
            audit.present_new.append(new_objects.by_key[key])
        else:
            audit.missing_new.append(new_objects.by_key[key])

    for key in sorted((old_keys & new_keys & mod_keys), key=lambda item: new_objects.by_key[item].order_index):
        old_norm = normalize_for_compare(old_objects.by_key[key].raw, ignore_ai)
        new_norm = normalize_for_compare(new_objects.by_key[key].raw, ignore_ai)
        if old_norm == new_norm:
            continue
        mod_norm = normalize_for_compare(mod_objects.by_key[key].raw, ignore_ai)
        if mod_norm == new_norm:
            audit.changed_existing_matching.append(new_objects.by_key[key])
        else:
            audit.changed_existing_review.append(new_objects.by_key[key])

    for key in sorted((old_keys & new_keys) - mod_keys, key=lambda item: new_objects.by_key[item].order_index):
        old_norm = normalize_for_compare(old_objects.by_key[key].raw, ignore_ai)
        new_norm = normalize_for_compare(new_objects.by_key[key].raw, ignore_ai)
        if old_norm != new_norm:
            audit.changed_existing_absent.append(new_objects.by_key[key])

    return audit


def analyze_drift_file(rel_path: str, base_text: str, mod_text: str) -> DriftAudit:
    audit = DriftAudit(path=rel_path)
    base_objects = extract_objects(rel_path, base_text)
    mod_objects = extract_objects(rel_path, mod_text)

    for source_name, object_set in (("current base", base_objects), ("mod", mod_objects)):
        for diagnostic in object_set.diagnostics:
            audit.diagnostics.append(f"{source_name}: {diagnostic}")

    base_keys = set(base_objects.by_key)
    mod_keys = set(mod_objects.by_key)
    audit.missing_current = [
        base_objects.by_key[key]
        for key in sorted(base_keys - mod_keys, key=lambda item: base_objects.by_key[item].order_index)
    ]
    audit.mod_only_count = len(mod_keys - base_keys)

    if base_keys and base_keys <= mod_keys:
        base_sequence = list(base_objects.by_key)
        mod_sequence = [key for key in mod_objects.by_key if key in base_keys]
        if base_sequence != mod_sequence:
            for i, (base_key, mod_key) in enumerate(zip(base_sequence, mod_sequence), start=1):
                if base_key != mod_key:
                    audit.order_mismatch = (
                        f"first mismatch at shared object {i}: "
                        f"base has {base_objects.by_key[base_key].display}, "
                        f"mod has {mod_objects.by_key[mod_key].display}"
                    )
                    break
    return audit


def mod_overwritten_files(mod_root: Path) -> List[str]:
    files: List[str] = []
    for path in mod_root.rglob("*"):
        if not path.is_file():
            continue
        rel = norm_path(str(path.relative_to(mod_root)))
        if rel.startswith(".") or rel.startswith("tools/") or rel.startswith("agent-guidance/"):
            continue
        if path.suffix.lower() not in {".txt", ".lua"}:
            continue
        files.append(rel)
    return sorted(files)


def format_entries(entries: Sequence[ObjectEntry], max_items: int) -> List[str]:
    lines = []
    for entry in entries[:max_items]:
        lines.append(f"  - `{entry.display}` (base line {entry.line})")
    if len(entries) > max_items:
        lines.append(f"  - ... {len(entries) - max_items} more")
    return lines


def render_report(
    args: argparse.Namespace,
    changed: Sequence[ChangedFile],
    patch_audits: Sequence[FileAudit],
    drift_audits: Sequence[DriftAudit],
    skipped: Sequence[Tuple[str, str]],
    base_only: Sequence[str],
) -> str:
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: List[str] = []
    lines.append("# Dynamic AI MP Patch Audit")
    lines.append("")
    lines.append(f"- Generated: {now}")
    lines.append(f"- Mod root: `{args.mod_root}`")
    lines.append(f"- Base repo: `{args.base_repo}`")
    lines.append(f"- Base refs: `{args.old_ref}` -> `{args.new_ref}`")
    lines.append(f"- AI tuning helper dirs skipped: `{not args.include_ai}`")
    lines.append("- `common/ai_strategy` changes are reviewed by default and are not automatic merge candidates.")
    lines.append(f"- DAI files skipped: `{not args.include_dai}`")
    lines.append("")
    lines.append("## Agent Use")
    lines.append("")
    lines.append("- Treat `Missing new upstream objects` as the first merge queue.")
    lines.append("- Treat `Changed existing upstream objects` as review-only; apply the A/B/C rule before merging values.")
    lines.append("- Treat `Drift scan` as a long-term hygiene pass against current base, not necessarily a latest-patch diff.")
    lines.append("- Treat new or changed `ai_strategy` content as something to call out for review, not an automatic merge.")
    lines.append("- Keep new standalone objects in current-base order when adding them to the mod.")
    lines.append("")

    overwritten_count = len(patch_audits) + len(skipped)
    lines.append("## Patch File Overlap")
    lines.append("")
    lines.append(f"- Base changed files: `{len(changed)}`")
    lines.append(f"- Changed files overwritten by mod: `{overwritten_count}`")
    lines.append(f"- Changed files not overwritten by mod: `{len(base_only)}`")
    lines.append(f"- Skipped changed overwritten files: `{len(skipped)}`")
    lines.append("")

    missing_audits = [audit for audit in patch_audits if audit.missing_new]
    lines.append("## Missing New Upstream Objects")
    lines.append("")
    if not missing_audits:
        lines.append("No missing `B - A` objects were found in changed overwritten files.")
    for audit in missing_audits:
        lines.append(f"### `{audit.path}`")
        lines.append(f"Missing: `{len(audit.missing_new)}`")
        lines.extend(format_entries(audit.missing_new, args.max_items))
        lines.append("")

    review_audits = [audit for audit in patch_audits if audit.changed_existing_review]
    lines.append("")
    lines.append("## Changed Existing Upstream Objects")
    lines.append("")
    if not review_audits:
        lines.append("No changed existing upstream objects need review after the default AI-block normalization.")
    for audit in review_audits:
        lines.append(f"### `{audit.path}`")
        lines.append(f"Review candidates: `{len(audit.changed_existing_review)}`")
        lines.extend(format_entries(audit.changed_existing_review, args.max_items))
        lines.append("")

    absent_review_audits = [audit for audit in patch_audits if audit.changed_existing_absent]
    lines.append("")
    lines.append("## Changed Existing Upstream Objects Absent From Mod")
    lines.append("")
    if not absent_review_audits:
        lines.append("No changed existing upstream objects were absent from the mod in changed overwritten files.")
    for audit in absent_review_audits:
        lines.append(f"### `{audit.path}`")
        if is_ai_strategy_path(audit.path):
            lines.append("These are strategy review notes only; do not merge automatically.")
        lines.append(f"Changed upstream objects absent from mod: `{len(audit.changed_existing_absent)}`")
        lines.extend(format_entries(audit.changed_existing_absent, args.max_items))
        lines.append("")

    matching = sum(len(audit.changed_existing_matching) for audit in patch_audits)
    if matching:
        lines.append("")
        lines.append("## Already Matching Upstream Changes")
        lines.append("")
        lines.append(f"`{matching}` changed existing upstream objects already match the mod after normalization.")
        lines.append("")

    drift_missing = [audit for audit in drift_audits if audit.missing_current]
    lines.append("")
    lines.append("## Drift Scan: Missing Current-Base Objects")
    lines.append("")
    if not drift_missing:
        lines.append("No missing current-base objects were found in high-value overwritten files.")
    for audit in drift_missing:
        lines.append(f"### `{audit.path}`")
        lines.append(f"Missing: `{len(audit.missing_current)}`")
        lines.extend(format_entries(audit.missing_current, args.max_items))
        lines.append("")

    order_mismatches = [audit for audit in drift_audits if audit.order_mismatch]
    lines.append("")
    lines.append("## Drift Scan: Base-Order Mismatches")
    lines.append("")
    if not order_mismatches:
        lines.append("No base-order mismatches were found for files with complete base object coverage.")
    for audit in order_mismatches[: args.max_files]:
        lines.append(f"- `{audit.path}`: {audit.order_mismatch}")
    if len(order_mismatches) > args.max_files:
        lines.append(f"- ... {len(order_mismatches) - args.max_files} more")

    diagnostic_lines = []
    for audit in list(patch_audits) + list(drift_audits):
        for diagnostic in audit.diagnostics:
            diagnostic_lines.append((audit.path, diagnostic))
    lines.append("")
    lines.append("## Diagnostics")
    lines.append("")
    if not diagnostic_lines:
        lines.append("No parser diagnostics.")
    for path, diagnostic in diagnostic_lines[: args.max_items]:
        lines.append(f"- `{path}`: {diagnostic}")
    if len(diagnostic_lines) > args.max_items:
        lines.append(f"- ... {len(diagnostic_lines) - args.max_items} more")

    lines.append("")
    lines.append("## Skipped Changed Overwritten Files")
    lines.append("")
    if not skipped:
        lines.append("None.")
    for path, reason in skipped:
        lines.append(f"- `{path}`: {reason}")

    lines.append("")
    lines.append("## Base Changed But Not Overwritten")
    lines.append("")
    if not base_only:
        lines.append("None.")
    for path in base_only[: args.max_files]:
        lines.append(f"- `{path}`")
    if len(base_only) > args.max_files:
        lines.append(f"- ... {len(base_only) - args.max_files} more")

    lines.append("")
    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit HOI4 base patch changes and current-base drift against Dynamic AI MP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Agent note: run this before patch-merging. Start with missing B-A objects, "
            "then review changed existing objects only under the patch-merge rules."
        ),
    )
    parser.add_argument("--mod-root", default=".", help="Path to dynamic-ai-mp. Default: current directory.")
    parser.add_argument("--base-repo", default="../hoi4-ai-base", help="Path to the vanilla/base tracking repo.")
    parser.add_argument("--old-ref", default="HEAD~1", help="Old base ref. Default: HEAD~1 in base repo.")
    parser.add_argument("--new-ref", default="HEAD", help="New/current base ref. Default: HEAD in base repo.")
    parser.add_argument("--write", help="Write Markdown report to this path instead of stdout.")
    parser.add_argument("--include-ai", action="store_true", help="Include common/ai_* tuning files.")
    parser.add_argument("--include-dai", action="store_true", help="Include DAI_* mod-specific files in drift scan.")
    parser.add_argument("--no-drift-scan", action="store_true", help="Disable current-base drift scan.")
    parser.add_argument("--no-ignore-ai-blocks", action="store_true", help="Do not strip ai_will_do blocks for changed-object comparison.")
    parser.add_argument("--max-items", type=int, default=30, help="Maximum object entries per report section.")
    parser.add_argument("--max-files", type=int, default=60, help="Maximum file entries per report section.")
    parser.add_argument("--fail-on-missing", action="store_true", help="Exit 2 if missing objects are found.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    args.mod_root = str(Path(args.mod_root).resolve())
    args.base_repo = str(Path(args.base_repo).resolve())
    mod_root = Path(args.mod_root)
    base_repo = Path(args.base_repo)

    if not mod_root.is_dir():
        raise SystemExit(f"mod root not found: {mod_root}")
    if not base_repo.is_dir():
        raise SystemExit(f"base repo not found: {base_repo}")

    changes = changed_files(base_repo, args.old_ref, args.new_ref)
    patch_audits: List[FileAudit] = []
    skipped: List[Tuple[str, str]] = []
    base_only: List[str] = []

    for change in changes:
        rel_path = change.path
        mod_text = read_mod_text(mod_root, rel_path)
        if mod_text is None:
            base_only.append(rel_path)
            continue
        if is_ai_tuning_path(rel_path) and not args.include_ai:
            skipped.append((rel_path, "AI tuning path; rerun with --include-ai to inspect"))
            continue
        if is_mod_specific_path(rel_path) and not args.include_dai:
            skipped.append((rel_path, "DAI_* mod-specific path"))
            continue
        old_text = git_text(base_repo, args.old_ref, change.old_path or rel_path)
        new_text = git_text(base_repo, args.new_ref, rel_path)
        patch_audits.append(
            analyze_patch_file(
                rel_path,
                old_text,
                new_text,
                mod_text,
                ignore_ai=not args.no_ignore_ai_blocks,
            )
        )

    drift_audits: List[DriftAudit] = []
    if not args.no_drift_scan:
        for rel_path in mod_overwritten_files(mod_root):
            if not is_high_value_path(rel_path):
                continue
            if is_ai_tuning_path(rel_path) and not args.include_ai:
                continue
            if is_mod_specific_path(rel_path) and not args.include_dai:
                continue
            base_text = git_text(base_repo, args.new_ref, rel_path)
            mod_text = read_mod_text(mod_root, rel_path)
            if base_text is None or mod_text is None:
                continue
            drift_audits.append(analyze_drift_file(rel_path, base_text, mod_text))

    report = render_report(args, changes, patch_audits, drift_audits, skipped, base_only)
    if args.write:
        out_path = Path(args.write)
        if not out_path.is_absolute():
            out_path = mod_root / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8", newline="\n")
        print(f"Wrote {out_path}")
    else:
        print(report)

    missing_count = sum(len(audit.missing_new) for audit in patch_audits)
    missing_count += sum(len(audit.missing_current) for audit in drift_audits)
    if args.fail_on_missing and missing_count:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
