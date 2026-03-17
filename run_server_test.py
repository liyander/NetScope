
import threading
import time
import requests
import json
import monitor
from werkzeug.serving import make_server

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server("127.0.0.1", 8050, app)

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

s = ServerThread(monitor.app.server)
s.start()
time.sleep(2)
try:
    print("Sending POST to _dash-update-component")
    res = requests.post(
        "http://127.0.0.1:8050/_dash-update-component",
        json={"output": "..page-content.children...link-dashboard.className...link-logs.className..", "outputs": {"page-content.children": {"id": "page-content", "property": "children"}, "link-dashboard.className": {"id": "link-dashboard", "property": "className"}, "link-logs.className": {"id": "link-logs", "property": "className"}}, "inputs": [{"id": "url", "property": "pathname", "value": "/logs"}], "changedPropIds": ["url.pathname"]}
    )
    print("STATUS", res.status_code)
    print(res.text)
finally:
    s.shutdown()

