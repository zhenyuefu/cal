from datetime import date
from os.path import join
from ics import Calendar
import requests

user = ("student.master", "guest")

url = {
    "AND": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/ANDROIDE/M1_ANDROIDE/",
    "DAC": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/DAC/M1_DAC/",
    "STL": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/STL/M1_STL/",
    "IMA": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/IMA/M1_IMA/",
    "BIM": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/BIM/M1_BIM/",
    "SAR": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/SAR/M1_SAR/",
    "SESI": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/SESI/M1_SESI/",
    "SFPN": "https://cal.ufr-info-p6.jussieu.fr/caldav.php/SFPN/M1_SFPN/",
}

cal = dict()


def get_remote(ue):
    cal[ue] = Calendar(requests.get(url[ue], auth=user).text)


def remove_events_before(c: Calendar, date: date):
    for event in c.timeline.__iter__():
        if event.begin is not None and event.begin.date() < date:
            c.events.remove(event)


def save():
    for ue in cal.keys():
        with open(join("data", ue + ".ics"), "w") as f:
            f.write(cal[ue].serialize())


start_date = date.fromisoformat("2022-09-04")

def fix_SFPN():
    for event in cal["SFPN"].timeline.__iter__():
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


for name in url.keys():
    get_remote(name)
    remove_events_before(cal[name], start_date)
    if name == "SFPN":
        fix_SFPN()
    save()
