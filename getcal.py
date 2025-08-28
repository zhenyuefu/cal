from datetime import date, datetime
from os.path import join
import json
import re

import requests
from ics import Calendar
from api.data import parcours_s1, parcours_s2, parcours_s3

user = ("student.master", "guest")
all_ue = ["ANDROIDE", "DAC", "STL", "IMA", "BIM", "SAR", "SESI", "SFPN"]
start_date = date.fromisoformat("2024-08-30")
cal = dict()


def get_url(ue, master_year):
    return f"https://cal.ufr-info-p6.jussieu.fr/caldav.php/{ue}/{master_year}_{ue}/"


def get_remote(ue, master_year):
    cal[f"{ue}{master_year}"] = Calendar(
        requests.get(get_url(ue, master_year), auth=user, verify=False).text
    )


def remove_events_before(c: Calendar, date: date):
    for event in c.timeline.__iter__():
        if event.begin is not None and event.begin.date() < date:
            c.events.remove(event)


def save(ue, master_year):
    if ue == "ANDROIDE":
        ues = "AND"
    else:
        ues = ue
    with open(join("data", f"{master_year}_{ues}.ics"), "w") as f:
        f.write(cal[f"{ue}{master_year}"].serialize())


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


def summary_to_code_label(summary: str):
    # Try MU/UM code pattern then label after first '-'
    m = re.match(r"^(?:MU|UM)([0-9A-Z]+)-([^-]+)", summary)
    if m:
        raw = m.group(1)  # e.g., 4IN811, 4LVAN2, 5IN861, 5INOIP
        label = m.group(2)
        # Specials
        if label.lower().startswith("anglais") or raw.startswith("4LV"):
            return "Anglais", "Anglais"
        if label.upper() == "OIP" or raw.upper().endswith("OIP"):
            return "OIP", "OIP"
        code = raw
        return code, label
    # Stage without MU code
    if re.search(r"stage", summary, flags=re.IGNORECASE):
        return "Stage", "Stage"
    return None, None


def extract_group_num(summary: str):
    # TD/TME/TP or GR/Grp patterns
    m = re.search(r"-(?:TD|TME|TP)\s*(\d+)", summary, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"[\s-][Gg][RrPp]?[\s]*(\d+)", summary)
    return int(m.group(1)) if m else None


def build_courses_catalog():
    # Build mapping for s1/s2 from parcours_s1/parcours_s2 and infer codes from ICS
    catalog = {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "s1": {},
        "s2": {},
        "s3": {},
    }

    # Helper: scan calendars for first code/label matching given label token
    def find_code_for_label_m1(label: str):
        for key, c in cal.items():
            if not key.endswith("M1"):
                continue
            for ev in c.events:
                if ev.summary and f"-{label}-" in ev.summary:
                    code, lbl = summary_to_code_label(ev.summary)
                    if code and code not in ("Anglais", "Stage"):
                        return code, lbl
        return None, None

    # Helper: find label for a given MU-less code by scanning M2 calendars
    def find_label_for_code_m2(code: str):
        for key, c in cal.items():
            if not key.endswith("M2"):
                continue
            for ev in c.events:
                if ev.summary and re.match(rf"^(?:MU|UM){re.escape(code)}-", ev.summary):
                    _code, lbl = summary_to_code_label(ev.summary)
                    if _code == code and lbl:
                        return lbl
        return code

    # Fill M1 s1/s2
    for name, parcours in parcours_s1.items():
        code, lbl = find_code_for_label_m1(name)
        if not code:
            continue
        catalog["s1"][code] = {"label": lbl or name, "parcours": parcours, "groups": 1}

    for name, parcours in parcours_s2.items():
        # Some entries in s2 are already codes like MU4IN202 or labels like DJ
        code, lbl = (None, None)
        m = re.match(r"^(?:MU|UM)([0-9A-Z]+)$", name)
        if m:
            code = m.group(1)
            lbl = None
        else:
            code, lbl = find_code_for_label_m1(name)
        if not code:
            continue
        catalog["s2"][code] = {"label": lbl or name, "parcours": parcours, "groups": 1}

    # Fill M2 s3 using parcours_s3 keys (mostly MU5IN codes)
    for key, parcours in parcours_s3.items():
        m = re.match(r"^(?:MU|UM)([0-9A-Z]+)$", key)
        if not m:
            continue
        code = m.group(1)
        label = find_label_for_code_m2(code)
        catalog["s3"][code] = {"label": label, "parcours": parcours, "groups": 1}

    # Add OIP if present in calendars
    oip_found = False
    for key, c in cal.items():
        if not key.endswith("M2"):
            continue
        for ev in c.events:
            if ev.summary and ("OIP" in ev.summary or "MU5INOIP" in ev.summary):
                oip_found = True
                break
        if oip_found:
            break
    if oip_found:
        catalog["s3"]["OIP"] = {"label": "OIP", "parcours": "IMA", "groups": 1}

    # Compute max groups for all codes by scanning events
    for key, c in cal.items():
        year = "s1" if key.endswith("M1") else "s3"
        if key.endswith("M1"):
            sem_targets = ("s1", "s2")
        else:
            sem_targets = ("s3",)
        for ev in c.events:
            if not ev.summary:
                continue
            code, lbl = summary_to_code_label(ev.summary)
            if not code:
                continue
            for sem in sem_targets:
                if code in catalog[sem]:
                    g = extract_group_num(ev.summary)
                    if g and g > (catalog[sem][code]["groups"] or 1):
                        catalog[sem][code]["groups"] = g

    with open(join("data", "courses.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)


# Build the JSON catalog after calendars are saved
build_courses_catalog()


def build_event_index():
    index: dict[str, dict[str, dict]] = {"M1": {}, "M2": {}}

    for name in all_ue:
        for M in ["M1", "M2"]:
            key = f"{name}{M}"
            c = cal[key]
            bucket = index[M].setdefault(name, {"events": {}})
            for ev in c.events:
                summary = ev.summary or ""
                code, label = summary_to_code_label(summary)
                # Flags
                s_lower = summary.lower()
                is_ang = "anglais" in s_lower or "mu4lvan" in s_lower
                is_conf = "conférence" in summary or "conference" in s_lower
                is_parcours = name in summary
                group = extract_group_num(summary)
                uid = getattr(ev, "uid", None)
                if not uid:
                    # Fallback UID-like string
                    uid = f"{ev.begin}-{summary}"
                bucket["events"][uid] = {
                    "code": code,  # e.g., 4IN204 / 5IN861 / OIP / None
                    "group": group,  # int or None
                    "isAnglais": is_ang,
                    "isConference": is_conf,
                    "isParcours": is_parcours,
                }

    with open(join("data", "event_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)


# Build the event index after calendars are saved
build_event_index()


def build_calendars_json():
    def ev_to_json(ev, parcours_name: str):
        summary = ev.summary or ""
        code, label = summary_to_code_label(summary)
        s_lower = summary.lower()
        return {
            "uid": getattr(ev, "uid", None),
            "begin": ev.begin.isoformat() if getattr(ev, "begin", None) else None,
            "end": ev.end.isoformat() if getattr(ev, "end", None) else None,
            "summary": summary,
            "location": getattr(ev, "location", None),
            "description": getattr(ev, "description", None),
            "sequence": getattr(ev, "sequence", None),
            # Derived fields
            "code": code,  # e.g., 4IN204 / 5IN861 / OIP / None
            "group": extract_group_num(summary),
            "isAnglais": ("anglais" in s_lower or "mu4lvan" in s_lower),
            "isConference": ("conférence" in summary or "conference" in s_lower),
            "isParcours": parcours_name in summary,
        }

    for name in all_ue:
        for M in ["M1", "M2"]:
            c = cal[f"{name}{M}"]
            parcours_name = "AND" if name == "ANDROIDE" else name
            events = [ev_to_json(ev, parcours_name) for ev in c.timeline.__iter__()]
            payload = {
                "calendarName": f"{M} {parcours_name}",
                "year": M,
                "parcours": parcours_name,
                "events": events,
            }
            with open(join("data", f"{M}_{parcours_name}.json"), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)


# Build flattened per-parcours calendar JSON files
build_calendars_json()
