from urllib import request
from http.server import BaseHTTPRequestHandler
from os.path import join


url_AND = "https://cal.ufr-info-p6.jussieu.fr/caldav.php/ANDROIDE/M1_ANDROIDE/"
url_DAC = "https://cal.ufr-info-p6.jussieu.fr/caldav.php/DAC/M1_DAC/"
url_STL = "https://cal.ufr-info-p6.jussieu.fr/caldav.php/STL/M1_STL/"
url_IMA = "https://cal.ufr-info-p6.jussieu.fr/caldav.php/IMA/M1_IMA/"
user = ("student.master", "guest")


def get_ics(url, name):
    with open(join("data", name), "w") as f:
        f.write(request.get(url, auth=user).text)


def get():
    get_ics(url_AND, "AND.ics")
    get_ics(url_DAC, "DAC.ics")
    get_ics(url_STL, "STL.ics")
    get_ics(url_IMA, "IMA.ics")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        get()
        self.end_headers()
        self.wfile.write("Hello World !".encode("utf-8"))
        return
