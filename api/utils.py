from ics import Calendar
from os.path import join
from urllib.parse import parse_qsl, urlparse
from http.server import BaseHTTPRequestHandler


def load_calendar(name: str, year="M1"):
    with open(join("data", f"{year}_{name}.ics"), "r") as f:
        return Calendar(f.read())


def filter_ue_parcours(ue: dict, parcours: dict):
    parcours_ue: dict[str, list[str]] = dict()
    for ue_name in ue.keys():
        if parcours[ue_name] in parcours_ue.keys():
            parcours_ue[parcours[ue_name]].append(ue_name)
        else:
            parcours_ue[parcours[ue_name]] = [ue_name]
    return parcours_ue


def handle_get(request, filter_cours_function, major_key="MAJ"):
    request.send_response(200)
    request.send_header("Content-type", 'text/xml; charset="utf-8"')
    request.send_header("Cache-Control", "s-maxage=1, stale-while-revalidate")
    request.end_headers()
    url = urlparse(request.path)
    query = parse_qsl(url.query)
    ues = dict(query)
    major = ues.pop(major_key)
    cal = filter_cours_function(ues, major)
    request.wfile.write(cal.serialize().encode())
    return
