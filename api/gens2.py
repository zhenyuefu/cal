import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler

from ics import Calendar, Container, ContentLine

from api.data import parcours_s2
from api.utils import filter_ue_parcours, handle_get, load_calendar
from api.index_loader import load_index_or_none, build_ics

start_date = datetime.fromisoformat("2024-01-11T12:05:23+02:00")

CALENDARS: dict[str, Calendar] = {}
FILTERED_EVENTS: dict[str, list] = {}
IS_INDEX_MODE: dict[str, bool] = {}


def _ensure_parcour_loaded(parcour: str):
    if parcour in FILTERED_EVENTS:
        return
    indexed = load_index_or_none("M1", parcour)  # S2 仍用 M1 文件命名规则
    if indexed is not None:
        FILTERED_EVENTS[parcour] = indexed  # type: ignore
        IS_INDEX_MODE[parcour] = True
        return
    cal = load_calendar(parcour)
    CALENDARS[parcour] = cal
    FILTERED_EVENTS[parcour] = list(cal.timeline.start_after(start_date))
    IS_INDEX_MODE[parcour] = False


def _iter_events_for_parcour(parcour: str):
    _ensure_parcour_loaded(parcour)
    return FILTERED_EVENTS.get(parcour, [])


def filter_cours(ue_group: dict, majour: str):

    parcours_ue = filter_ue_parcours(ue_group, parcours_s2)

    # 预编译正则
    compiled_patterns: dict[str, re.Pattern] = {}
    for ue_name, group_code in ue_group.items():
        try:
            compiled_patterns[ue_name] = re.compile(rf"T\w{{1,2}}(?=\d)(?!{group_code})")
        except re.error:
            compiled_patterns[ue_name] = re.compile(r"^$")

    # 判定是否所有 parcours 都为索引模式
    all_index = True
    for parcour in parcours_ue.keys():
        _ensure_parcour_loaded(parcour)
        if not IS_INDEX_MODE.get(parcour):
            all_index = False
            break

    if not all_index:
        cal = Calendar()
        cal.extra = Container(
            "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M1 " + majour)]
        )
    else:
        cal = None  # type: ignore

    collected_index_events: list[dict] = []

    for parcour in parcours_ue.keys():
        for event in _iter_events_for_parcour(parcour):
            summary = getattr(event, "summary", "") if not IS_INDEX_MODE.get(parcour) else event.get("summary", "")  # type: ignore

            if majour == parcour and (
                parcour in summary
                or "MU4LVAN2" in summary
                or "MU4LV001" in summary
                or "Conférence" in summary
            ):
                if IS_INDEX_MODE.get(parcour):
                    collected_index_events.append(event)  # type: ignore
                else:
                    cal.events.add(event)  # type: ignore
                continue

            for ue in parcours_ue[parcour]:
                if ue in summary:
                    if IS_INDEX_MODE.get(parcour):
                        groups = event.get("groups", [])  # type: ignore
                        target = ue_group.get(ue)
                        if groups and not (set(groups) == {target}):
                            continue
                        collected_index_events.append(event)  # type: ignore
                    else:
                        pattern = compiled_patterns.get(ue)
                        if pattern and pattern.search(summary):
                            continue
                        cal.events.add(event)  # type: ignore
                    break
    if cal is not None:
        return cal

    ics_text = build_ics("M1 " + majour, collected_index_events)
    class _Wrapper:
        def __init__(self, text: str):
            self._t = text
        def serialize(self):
            return self._t
    return _Wrapper(ics_text)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        handle_get(self, filter_cours)
