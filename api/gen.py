from http.server import BaseHTTPRequestHandler

from os.path import join
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from ics import Calendar

cal = dict()
start_date = datetime.fromisoformat("2022-09-04T12:05:23+02:00")
parcours = {"MOGPL": "AND", "IL": "STL", "LRC": "DAC", "MLBDA": "DAC", "MAPSI": "IMA"}


def load_calendar(name: str):
    with open(join("data", name + ".ics"), "r") as f:
        cal[name] = Calendar(f.read())


def filter_cours(ue: dict, majour: str):
    cal = Calendar()
    iter_and = AND.timeline.start_after(start_date)
    for event in iter_and:
        if MOGPL != 0 and "MOGPL" in event.summary:
            pattern = "T\w{1,2}(?=\d)(?!" + str(MOGPL) + ")"
            if re.search(pattern, event.summary):
                continue
            cal.events.append(event)
        if "AND" in event.summary:
            cal.events.append(event)

    iter_stl = STL.timeline.start_after(start_date)
    for event in iter_stl:
        if IL != 0 and "IL" in event.summary:
            pattern = "T\w{1,2}(?=\d)(?!" + str(IL) + ")"
            if re.search(pattern, event.summary):
                continue
            cal.events.append(event)

    iter_dac = DAC.timeline.start_after(start_date)
    for event in iter_dac:
        if LRC != 0 and "LRC" in event.summary:
            pattern = "T\w{1,2}(?=\d)(?!" + str(LRC) + ")"
            if re.search(pattern, event.summary, 0):
                continue
            cal.events.append(event)

        if MLBDA != 0 and "MLBDA" in event.summary:
            pattern = "T\w{1,2}(?=\d)(?!" + str(MLBDA) + ")"
            if re.search(pattern, event.summary, 0):
                continue
            cal.events.append(event)

    iter_ima = IMA.timeline.start_after(start_date)
    for event in iter_ima:
        if MAPSI != 0 and "MAPSI" in event.summary:
            pattern = "T\w{1,2}(?=\d)(?!" + str(MAPSI) + ")"
            if re.search(pattern, event.summary, 0):
                continue
            cal.events.append(event)

    return cal


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", 'text/xml; charset="utf-8"')
        self.send_header("Cache-Control", "s-maxage=259200")
        self.end_headers()
        url = urlparse(self.path)
        query = parse_qs(url.query)
        cal = filter_cours(3, 2, 1, 1, 3)
        self.wfile.write(cal.serialize().encode())
        return
