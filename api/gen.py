import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler

from ics import Calendar, Container, ContentLine

from api.data import parcours_s1
from api.utils import filter_ue_parcours, handle_get, load_calendar

start_date = datetime.fromisoformat("2023-09-04T12:05:23+02:00")
CALENDARS: dict[str, Calendar] = dict()


def filter_cours(ue_group: dict, majour: str):
    cal = Calendar()
    cal.extra = Container(
        "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M1 " + majour)]
    )
    parcours_ue = filter_ue_parcours(ue_group, parcours_s1)
    for parcour in parcours_ue.keys():
        CALENDARS[parcour] = load_calendar(parcour)
        iter_parcour = CALENDARS[parcour].timeline.start_after(start_date)
        for event in iter_parcour:
            if "anglais" in event.summary or "Anglais" in event.summary:
                continue
            if majour == parcour:
                if parcour in event.summary:
                    cal.events.append(event)
                    continue
            for ue in parcours_ue[parcour]:
                if ue in event.summary:
                    pattern = "T\w{1,2}(?=\d)(?!" + str(ue_group[ue]) + ")"
                    if not re.search(pattern, event.summary):
                        cal.events.append(event)
                        break
    return cal


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        handle_get(self, filter_cours)
