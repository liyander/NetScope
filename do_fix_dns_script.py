import re

with open("monitor_new.py", "r", encoding="utf-8") as f:
    text = f.read()

dns_func = """import socket
import concurrent.futures

dns_cache = {}
def get_hostname(ip):
    if not ip or ip in ("127.0.0.1", "0.0.0.0", "::1"):
        return ip
    if ip in dns_cache:
        return dns_cache[ip]

    def resolve():
        try:
            name = socket.gethostbyaddr(ip)[0]
            return name
        except Exception:
            return ip

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(resolve)
        try:
            hostname = future.result(timeout=0.1)
            dns_cache[ip] = hostname
            return hostname
        except Exception:
            dns_cache[ip] = ip
            return ip
"""

if "def get_hostname" not in text:
    text = text.replace("import csv", dns_func + "\nimport csv", 1)

# fix update_data list
text = text.replace(
    'laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else ""',
    'laddr = f"{get_hostname(c.laddr.ip)}:{c.laddr.port}" if c.laddr else ""'
)
text = text.replace(
    'raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else ""',
    'raddr = f"{get_hostname(c.raddr.ip)}:{c.raddr.port}" if c.raddr else ""'
)

# fix update_dashboard_views table
text = text.replace(
    'laddr = f"{c.laddr.ip}" if c.laddr else "127.0.0.1"',
    'laddr = f"{get_hostname(c.laddr.ip)}" if c.laddr else "127.0.0.1"'
)
text = text.replace(
    'raddr_ip = f"{c.raddr.ip}" if c.raddr else "Local Network"',
    'raddr_ip = f"{get_hostname(c.raddr.ip)}" if c.raddr else "Local Network"'
)

with open("monitor_new.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Done styling monitor_new.py")
