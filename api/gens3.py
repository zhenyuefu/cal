from datetime import datetime
from http.server import BaseHTTPRequestHandler

from ics import Calendar, Container, ContentLine, Event

from api.utils import (
    filter_ue_parcours,
    handle_get,
    load_courses_mapping,
    load_calendar_events,
)

start_date = datetime.fromisoformat("2023-09-10T12:05:23+02:00")
CALENDARS: dict[str, Calendar] = dict()


def filter_cours(ue_group: dict, majour: str):
    cal = Calendar()
    # 设置日历的名称
    cal.extra = Container(
        "VCALENDAR", [ContentLine("X-WR-CALNAME", value="M2 " + majour)]
    )

    # Load mapping and add OIP dynamically to selected major if requested
    courses_map = load_courses_mapping("s3")
    if "OIP" in ue_group:
        courses_map["OIP"] = majour
    # 建立字典，存储课程是哪一个专业的
    parcours_ue = filter_ue_parcours(ue_group, courses_map)

    # 遍历专业，将专业对应的课程加入到日历中
    for parcour in parcours_ue.keys():
        events = load_calendar_events("M2", parcour)
        for info in events:
            try:
                if info.get("begin") and datetime.fromisoformat(info["begin"]).timestamp() < start_date.timestamp():
                    continue
            except Exception:
                pass
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
