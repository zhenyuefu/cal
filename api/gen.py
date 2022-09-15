from http.server import BaseHTTPRequestHandler
from itertools import count

from os.path import join
import re
from datetime import datetime
from urllib.parse import parse_qs, parse_qsl, urlparse

from ics import Calendar, Container, ContentLine

CALENDARS: dict[str, Calendar] = dict()
start_date = datetime.fromisoformat("2022-09-04T12:05:23+02:00")
parcours = {"MOGPL": "AND", "IL": "STL", "LRC": "DAC", "MLBDA": "DAC", "MAPSI": "IMA"}


def load_calendar(name: str):
    with open(join("data", name + ".ics"), "r") as f:
        CALENDARS[name] = Calendar(f.read())


def filter_ue_parcours(ue: dict):
    parcours_ue: dict[str, list[str]] = dict()
    for ue_name in ue.keys():
        if parcours_ue[ue_name] in parcours_ue.keys():
            parcours_ue[parcours[ue_name]].append(ue_name)
        else:
            parcours_ue[parcours[ue_name]] = [ue_name]
    return parcours_ue


def filter_cours(ue_group: dict, majour: str):
    cal = Calendar()
    cal.extra = Container(
        "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M1 " + majour)]
    )
    parcours_ue = filter_ue_parcours(ue_group)
    for parcour in parcours_ue.keys():
        load_calendar(parcour)
        iter_parcour = CALENDARS[parcour].timeline.start_after(start_date)
        for event in iter_parcour:
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
        self.send_response(200)
        self.send_header("Content-type", 'text/xml; charset="utf-8"')
        self.send_header("Cache-Control", "s-maxage=259200")
        self.end_headers()
        url = urlparse(self.path)
        query = parse_qsl(url.query)
        ues = dict(query)
        major = ues.pop("MAJ")
        cal = filter_cours(ues, major)
        self.wfile.write(cal.serialize().encode())
        return
