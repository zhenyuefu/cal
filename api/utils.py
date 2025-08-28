from os.path import join
import json
from urllib.parse import parse_qsl, urlparse
from http.server import BaseHTTPRequestHandler


# ICS files are no longer read at request time; calendars are stored as JSON


def filter_ue_parcours(ue: dict, parcours: dict):
    # Support trimmed keys like 5IN861/4IN202 in addition to MU5IN861/MU4IN202
    alias: dict[str, str] = dict(parcours)
    for k, v in list(parcours.items()):
        if len(k) >= 3 and (k[:2] == "MU" or k[:2] == "Um" or k[:2] == "UM" or k[:2] == "mu"):
            alias[k[2:]] = v  # e.g., MU5IN861 -> 5IN861

    parcours_ue: dict[str, list[str]] = dict()
    for ue_name in ue.keys():
        if ue_name not in alias:
            # If not found, skip silently (unknown UE key)
            continue
        dest = alias[ue_name]
        if dest in parcours_ue:
            parcours_ue[dest].append(ue_name)
        else:
            parcours_ue[dest] = [ue_name]
    return parcours_ue


def handle_get(request, filter_cours_function, major_key="MAJ"):
    request.send_response(200)
    request.send_header("Content-type", 'text/xml; charset="utf-8"')
    request.send_header("Cache-Control", "s-maxage=1, stale-while-revalidate")
    request.end_headers()
    url = urlparse(request.path)
    query = parse_qsl(url.query)
    ues = dict(query)
    major = ues.pop(major_key)
    cal = filter_cours_function(ues, major)
    request.wfile.write(cal.serialize().encode())
    return


_COURSES_JSON_CACHE = None


def load_courses_json():
    global _COURSES_JSON_CACHE
    if _COURSES_JSON_CACHE is None:
        with open(join("data", "courses.json"), "r", encoding="utf-8") as f:
            _COURSES_JSON_CACHE = json.load(f)
    return _COURSES_JSON_CACHE


_COURSES_MAP_CACHE: dict[str, dict] = {}


def load_courses_mapping(semester: str) -> dict:
    if semester in _COURSES_MAP_CACHE:
        return _COURSES_MAP_CACHE[semester]
    data = load_courses_json()
    if semester not in ("s1", "s2", "s3"):
        raise ValueError("semester must be one of s1, s2, s3")
    items = data.get(semester, {})
    # Return trimmed-code -> parcours mapping
    mapping = {code: items[code]["parcours"] for code in items}
    _COURSES_MAP_CACHE[semester] = mapping
    return mapping


_EVENT_INDEX_CACHE = None


def load_event_index(year: str, parcours: str) -> dict:
    global _EVENT_INDEX_CACHE
    if _EVENT_INDEX_CACHE is None:
        with open(join("data", "event_index.json"), "r", encoding="utf-8") as f:
            _EVENT_INDEX_CACHE = json.load(f)
    return _EVENT_INDEX_CACHE.get(year, {}).get(parcours, {}).get("events", {})


_CAL_JSON_CACHE: dict[str, dict] = {}


def load_calendar_events(year: str, parcours: str) -> list[dict]:
    key = f"{year}_{parcours}"
    if key not in _CAL_JSON_CACHE:
        with open(join("data", f"{key}.json"), "r", encoding="utf-8") as f:
            _CAL_JSON_CACHE[key] = json.load(f)
    return _CAL_JSON_CACHE[key].get("events", [])
