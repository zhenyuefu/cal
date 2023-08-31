from datetime import date
from os.path import join

import requests
from ics import Calendar

user = ("student.master", "guest")
all_ue = ["ANDROIDE", "DAC", "STL", "IMA", "BIM", "SAR", "SESI", "SFPN"]
start_date = date.fromisoformat("2023-09-01")
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


# def fix_SFPN():
#     for event in cal["SFPN"].timeline.__iter__():
#         if "MU4IN900-COMPLEX-TD" == event.summary:
#             event.summary = "MU4IN900-COMPLEX-TD1"
#             continue
#         if "MU4IN900-COMPLEX-TME" == event.summary:
#             event.summary = "MU4IN900-COMPLEX-TME1"
#             continue
#         if "MU4IN901-MODEL-TD" == event.summary:
#             event.summary = "MU4IN901-MODEL-TD1"
#             continue
#         if "MU4IN901-MODEL-TME" == event.summary:
#             event.summary = "MU4IN901-MODEL-TME1"
#             continue


for name in all_ue:
    for M in ["M1", "M2"]:
        get_remote(name, M)
        remove_events_before(cal[f"{name}{M}"], start_date)
        # if name == "SFPN" and M == "M1":
        #     fix_SFPN()
        save(name, M)
