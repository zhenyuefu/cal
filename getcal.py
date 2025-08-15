from datetime import date, timezone
from os.path import join, exists
import json
import os
import re

import requests
from ics import Calendar

user = ("student.master", "guest")
all_ue = ["ANDROIDE", "DAC", "STL", "IMA", "BIM", "SAR", "SESI", "SFPN"]
start_date = date.fromisoformat("2025-08-30")
cal = dict()


def get_url(ue, master_year):
    return f"https://cal.ufr-info-p6.jussieu.fr/caldav.php/{ue}/{master_year}_{ue}/"


def get_remote(ue, master_year):
    resp = requests.get(get_url(ue, master_year), auth=user, verify=False)
    # 强制使用 UTF-8 解析，防止服务器未声明编码导致后续写入问题
    if not resp.encoding:
        resp.encoding = "utf-8"
    cal[f"{ue}{master_year}"] = Calendar(resp.text)


def remove_events_before(c: Calendar, date: date):
    for event in c.timeline.__iter__():
        if event.begin is not None and event.begin.date() < date:
            c.events.remove(event)


def save(ue, master_year):
    if ue == "ANDROIDE":
        ues = "AND"
    else:
        ues = ue
    # 保存 ICS 文件
    ics_path = join("data", f"{master_year}_{ues}.ics")
    with open(ics_path, "w", encoding="utf-8", newline="") as f:
        data_str = cal[f"{ue}{master_year}"].serialize()
        # 确保无法编码字符不会中断（极少数非法码点时 fallback）
        try:
            f.write(data_str)
        except UnicodeEncodeError:
            f.write(data_str.encode("utf-8", errors="ignore").decode("utf-8"))

    # 生成精简 JSON 索引（降低函数冷启动解析成本）
    index_dir = join("data", "index")
    if not exists(index_dir):
        os.makedirs(index_dir, exist_ok=True)
    json_path = join(index_dir, f"{master_year}_{ues}.json")
    events_index = []
    for ev in cal[f"{ue}{master_year}"].events:
        begin = ev.begin if getattr(ev, "begin", None) else None
        end = ev.end if getattr(ev, "end", None) else None
        # 预格式化成 ICS UTC 时间字符串，减少运行时转换
        dtstart_ics = (
            begin.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ") if begin else None
        )
        dtend_ics = (
            end.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ") if end else None
        )
        summary = ev.summary or ""
        # 提取组号：TD1 / TME2 / TP3 等形式 + GR1 / gr2
        groups = set()
        for m in re.finditer(r"T\w{1,2}(\d+)", summary):
            groups.add(m.group(1))
        for m in re.finditer(r"[Gg][Rr]\s*(\d+)", summary):
            groups.add(m.group(1))
        events_index.append(
            {
                "summary": summary,
                "begin": begin.isoformat() if begin else None,
                "end": end.isoformat() if end else None,
                "dtstart": dtstart_ics,
                "dtend": dtend_ics,
                "groups": sorted(groups),
                "location": getattr(ev, "location", None),
                "description": getattr(ev, "description", None),
            }
        )
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(events_index, jf, ensure_ascii=False, separators=(",", ":"))


def fix_SFPN():
    for event in cal["SFPNM1"].timeline.__iter__():
        if "MU4IN900-COMPLEX-TD" == event.summary:
            event.summary = "MU4IN900-COMPLEX-TD1"
            continue
        if "MU4IN900-COMPLEX-TME" == event.summary:
            event.summary = "MU4IN900-COMPLEX-TME1"
            continue
        if "MU4IN901-MODEL-TD" == event.summary:
            event.summary = "MU4IN901-MODEL-TD1"
            continue
        if "MU4IN901-MODEL-TME" == event.summary:
            event.summary = "MU4IN901-MODEL-TME1"
            continue


for name in all_ue:
    for M in ["M1", "M2"]:
        get_remote(name, M)
        remove_events_before(cal[f"{name}{M}"], start_date)
        if name == "SFPN" and M == "M1":
            fix_SFPN()
        save(name, M)
