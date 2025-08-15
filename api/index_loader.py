import json
from os.path import join, exists
from typing import List, Dict, Any

_cache: dict[str, List[Dict[str, Any]]] = {}


def load_index_or_none(year_prefix: str, parcour: str):
    key = f"{year_prefix}_{parcour}"
    if key in _cache:
        return _cache[key]
    path = join("data", "index", f"{key}.json")
    if not exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # raw: list[dict]
    _cache[key] = raw
    return raw


def build_ics(calendar_name: str, events: List[Dict[str, Any]]):
    # Minimal VCALENDAR + VEVENT blocks (UTC times already preformatted)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"X-WR-CALNAME:{calendar_name}",
        "PRODID:-//prebuilt//calendar//EN",
    ]
    for ev in events:
        lines.append("BEGIN:VEVENT")
        if ev.get("dtstart"):
            lines.append(f"DTSTART:{ev['dtstart']}")
        if ev.get("dtend"):
            lines.append(f"DTEND:{ev['dtend']}")
        summary = ev.get("summary", "").replace("\n", " ")
        lines.append(f"SUMMARY:{summary}")
        if ev.get("location"):
            loc = str(ev.get("location")).replace("\n", " ")
            lines.append(f"LOCATION:{loc}")
        if ev.get("description"):
            desc = str(ev.get("description")).replace("\n", " ")
            lines.append(f"DESCRIPTION:{desc}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
