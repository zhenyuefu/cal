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


for name in url.keys():
    get_remote(name)
    remove_events_before(cal[name], start_date)
    save()
