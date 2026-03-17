import re

with open('monitor_new.py', 'r', encoding='utf-8') as f:
    text = f.read()

dns_func = '''import socket
import concurrent.futures

dns_cache = {}
def get_hostname(ip):
    if not ip or ip in ("127.0.0.1", "0.0.0.0", "::1"):
        return ip
    if ip in dns_cache:
        return dns_cache[ip]
    
    def resolve():
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ip
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(resolve)
        try:
            hostname = future.result(timeout=0.1)
            dns_cache[ip] = hostname
            return hostname
        except Exception:
            # timeout or other error
            dns_cache[ip] = ip
            return ip

'''

text = re.sub(r'(# Setup Logging)', dns_func + r'\1', text, count=1)

# In update_connections (for logs)
text = re.sub(
    r'laddr = f"\{c\.laddr\.ip\}:\{c\.laddr\.port\}" if c\.laddr else ""\s*raddr = f"\{c\.raddr\.ip\}:\{c\.raddr\.port\}" if c\.raddr else ""',
    r'laddr = f"{get_hostname(c.laddr.ip)}:{c.laddr.port}" if c.laddr else ""\n                    raddr = f"{get_hostname(c.raddr.ip)}:{c.raddr.port}" if c.raddr else ""',
    text
)

# In visual table
text = re.sub(
    r'laddr = f"\{c\.laddr\.ip\}" if c\.laddr else "127\.0\.0\.1"',
    r'laddr = f"{get_hostname(c.laddr.ip)}" if c.laddr else "127.0.0.1"',
    text
)
text = re.sub(
    r'raddr_ip = f"\{c\.raddr\.ip\}" if c\.raddr else "Local Network"',
    r'raddr_ip = f"{get_hostname(c.raddr.ip)}" if c.raddr else "Local Network"',
    text
)

with open('monitor_new.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("done")
