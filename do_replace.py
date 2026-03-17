import json

with open("old_str.txt", "r", encoding="utf-8") as f:
    old_str = f.read()

new_str = """        for i, c in enumerate(active_conns[:80]):
            laddr = f"{c.laddr.ip}" if c.laddr else "127.0.0.1"
            lport = f"{c.laddr.port}" if c.laddr else "-"
            raddr_ip = f"{c.raddr.ip}" if c.raddr else "Local Network"
            raddr_port = f"{c.raddr.port}" if c.raddr else "-"
            bg = "bg-green-500 animate-pulse" if c.status == "ESTABLISHED" else "bg-amber-500"
            if c.status == "LISTEN": bg = "bg-blue-500"
            if c.status == "TIME_WAIT": bg = "bg-slate-600"
            
            pid_val = getattr(c, "pid", "-")
            row_data = {
                "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                "protocol": "TCP" if getattr(c, "type", 1) == 1 else "UDP",
                "data": "1.2 KB",
                "msg": f"Status: {c.status} | PID: {pid_val}",
                "src_ip": laddr,
                "src_port": lport,
                "dst_ip": raddr_ip,
                "dst_port": raddr_port,
                "src_mac": "00:15:5d:0a:c0:3d",
                "dst_mac": "a4:b0:cb:11:22:33",
                "src_fqdn": f"Host-{laddr.replace('.', '-')}.local" if laddr else "localhost"
            }

            conn_rows.append(html.Tr(id={"type": "conn-row", "index": json.dumps(row_data)}, n_clicks=0, className="hover:bg-slate-800/50 cursor-pointer transition-colors border-b border-slate-800/50 group", children=[
                html.Td(laddr, className="px-6 py-3 font-mono text-sky-400 text-[13px] group-hover:text-sky-300"),
                html.Td(f"{raddr_ip}:{raddr_port}", className="px-6 py-3 font-mono text-[#fcb000] text-[13px] group-hover:text-yellow-400"),
                html.Td(html.Div(className="flex justify-end items-center gap-2", children=[
                    html.Span(c.status, className="text-[10px] text-slate-500"),
                    html.Span(className=f"inline-block w-2 h-2 shadow rounded-full {bg}")
                ]), className="px-6 py-3 text-right")
            ]))"""

with open("monitor_new.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(old_str, new_str)

with open("monitor_new.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Replaced!")
