from http.server import BaseHTTPRequestHandler

from os.path import join
import re
from datetime import datetime
from urllib.parse import parse_qs, parse_qsl, urlparse

from ics import Calendar, Container, ContentLine

CALENDARS: dict[str, Calendar] = dict()
start_date = datetime.fromisoformat("2023-01-21T12:05:23+02:00")
parcours = {
    "DJ"    : "AND",
    "FoSyMa": "AND",
    "MU4IN202": "AND",
    "IHM"   : "AND",
    "RP"    : "AND",
    "RA"    : "AND",
    "RITAL" : "DAC",
    "ML"    : "DAC",
    "MU4IN812": "DAC",
    "MU4IN811": "DAC",
    "IAMSI" : "DAC",
    "SAM"   : "DAC",
    "IG3D"  : "IMA"
}


def load_calendar(name: str):
    with open(join("data", name + ".ics"), "r") as f:
        CALENDARS[name] = Calendar(f.read())


def filter_ue_parcours(ue: dict):
    parcours_ue: dict[str, list[str]] = dict()
    for ue_name in ue.keys():
        if parcours[ue_name] in parcours_ue.keys():
            parcours_ue[parcours[ue_name]].append(ue_name)
        else:
            parcours_ue[parcours[ue_name]] = [ue_name]
    return parcours_ue


def filter_cours(ue_group: dict, majour: str):
    cal = Calendar()
    # 设置日历的名称
    cal.extra = Container(
        "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M1 " + majour)]
    )
    # 建立字典，存储课程是哪一个专业的
    parcours_ue = filter_ue_parcours(ue_group)
    # 遍历专业，将专业对应的课程加入到日历中
    for parcour in parcours_ue.keys():
        load_calendar(parcour)
        iter_parcour = CALENDARS[parcour].timeline.start_after(start_date)
        for event in iter_parcour:
            if majour == parcour:
                if parcour in event.summary or "MU4LVAN2" in event.summary or "MU4LV001" in event.summary or "Conférence" in event.summary:
                    cal.events.append(event)
                    continue
            if majour == "AND" and parcour == "DAC":
                if "Conférence" in event.summary:
                    cal.events.add(event)
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
        self.send_header("Cache-Control", "s-maxage=1, stale-while-revalidate")
        self.end_headers()
        url = urlparse(self.path)
        query = parse_qsl(url.query)
        ues = dict(query)
        major = ues.pop("MAJ")
        cal = filter_cours(ues, major)
        self.wfile.write(cal.serialize().encode())
        return
