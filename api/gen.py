from datetime import datetime
from http.server import BaseHTTPRequestHandler

from ics import Calendar, Container, ContentLine, Event

from api.utils import (
    filter_ue_parcours,
    handle_get,
    load_courses_mapping,
    load_calendar_events,
)

start_date = datetime.fromisoformat("2023-09-04T12:05:23+02:00")


def filter_cours(ue_group: dict, majour: str):
    cal = Calendar()
    cal.extra = Container(
        "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M1 " + majour)]
    )
    parcours_s1 = load_courses_mapping("s1")
    parcours_ue = filter_ue_parcours(ue_group, parcours_s1)
    for parcour in parcours_ue.keys():
        events = load_calendar_events("M1", parcour)
        for info in events:
            # Skip early events (defensive, JSON should already be filtered by date)
            try:
                if info.get("begin") and datetime.fromisoformat(info["begin"]).timestamp() < start_date.timestamp():
                    continue
            except Exception:
                pass
            if info.get("isAnglais"):
                continue
            if majour == parcour and info.get("isParcours"):
                ev = Event()
                ev.name = info.get("summary")
                ev.begin = info.get("begin")
                ev.end = info.get("end")
                ev.location = info.get("location")
                ev.description = info.get("description")
                ev.uid = info.get("uid")
                cal.events.add(ev)
                continue
            for ue in parcours_ue[parcour]:
                if info.get("code") != ue:
                    continue
                g = info.get("group")
                if g is None or str(g) == str(ue_group[ue]):
                    ev = Event()
                    ev.name = info.get("summary")
                    ev.begin = info.get("begin")
                    ev.end = info.get("end")
                    ev.location = info.get("location")
                    ev.description = info.get("description")
                    ev.uid = info.get("uid")
                    cal.events.add(ev)
                    break
    return cal


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        handle_get(self, filter_cours)
