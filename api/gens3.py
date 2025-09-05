import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler

from ics import Calendar, Container, ContentLine

from api.data import parcours_s3
from api.utils import filter_ue_parcours, handle_get, load_calendar

start_date = datetime.fromisoformat("2023-09-10T12:05:23+02:00")
CALENDARS: dict[str, Calendar] = dict()


def filter_cours(ue_group: dict, majour: str):
    cal = Calendar()
    # 设置日历的名称
    cal.extra = Container(
        "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M2 " + majour)]
    )

    # add oip to major
    parcours_s3["OIP"] = majour

    # 建立字典，存储课程是哪一个专业的
    parcours_ue = filter_ue_parcours(ue_group, parcours_s3)

    # 遍历专业，将专业对应的课程加入到日历中
    for parcour in parcours_ue.keys():
        CALENDARS[parcour] = load_calendar(parcour, "M2")
        iter_parcour = CALENDARS[parcour].timeline.start_after(start_date)
        for event in iter_parcour:
            if majour == parcour:
                if parcour in event.summary:
                    cal.events.append(event)
                    continue
            for ue in parcours_ue[parcour]:
                if ue in event.summary:
                    pattern = rf"T\w{{1,2}}(?:(?=\d)(?!{ue_group[ue]})|\s*[Gg][Rr](?!{ue_group[ue]}))"
                    if not re.search(pattern, event.summary):
                        cal.events.append(event)
                        break
    return cal


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        handle_get(self, filter_cours)
