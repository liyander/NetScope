import re

with open('monitor_new.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add id and dcc.Download to the Export button
text = re.sub(
    r'html\.Button\("Export Data", className="px-4 py-1\.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium transition-colors text-white shadow-sm border-0 cursor-pointer"\)',
    'html.Button("Export Data", id="btn-export", className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium transition-colors text-white shadow-sm border-0 cursor-pointer"),\n            dcc.Download(id="download-data")',
    text
)

# 2. Add Export callback
export_cb = '''
@app.callback(
    Output("download-data", "data"),
    Input("btn-export", "n_clicks"),
    prevent_initial_call=True
)
def export_data(n_clicks):
    import os
    if os.path.exists(LOG_FILE):
        return dcc.send_file(LOG_FILE)
    return dash.no_update
'''
if 'def export_data' not in text:
    text += export_cb

# 3. Add reverse DNS cache and DNS lookup logic in update_connections
header_imports = '''import socket
dns_cache = {}

def get_hostname(ip):
    if not ip or ip == "127.0.0.1" or ip == "0.0.0.0":
        return ip
    if ip in dns_cache:
        return dns_cache[ip]
    try:
        # short timeout for dns
        hostname = socket.gethostbyaddr(ip)[0]
        dns_cache[ip] = hostname
        return hostname
    except Exception:
        dns_cache[ip] = ip
        return ip
'''

# Find a good place to inject get_hostname: near the top, after imports
text = re.sub(r'# Global state to keep track of history', header_imports + '\n# Global state to keep track of history', text)

# Find the connections loop to inject hostname resolution
replace_target = '''            for c in current_conns:
                if c.status == 'ESTABLISHED':
                    laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else ""
                    raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else ""'''

replacement = '''            for c in current_conns:
                if c.status == 'ESTABLISHED':
                    laddr = f"{get_hostname(c.laddr.ip)}:{c.laddr.port}" if c.laddr else ""
                    raddr = f"{get_hostname(c.raddr.ip)}:{c.raddr.port}" if c.raddr else ""'''

text = text.replace(replace_target, replacement)

# Do the same for the visual connection table
replace_target_2 = '''        laddr_ip = conn.laddr.ip if conn.laddr else "N/A"
        laddr_port = conn.laddr.port if conn.laddr else ""
        raddr_ip = conn.raddr.ip if conn.raddr else "LISTEN"
        raddr_port = conn.raddr.port if conn.raddr else ""'''

replacement_2 = '''        laddr_ip = get_hostname(conn.laddr.ip) if conn.laddr else "N/A"
        laddr_port = conn.laddr.port if conn.laddr else ""
        raddr_ip = get_hostname(conn.raddr.ip) if conn.raddr else "LISTEN"
        raddr_port = conn.raddr.port if conn.raddr else ""'''

text = text.replace(replace_target_2, replacement_2)

with open('monitor_new.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Patched!")
