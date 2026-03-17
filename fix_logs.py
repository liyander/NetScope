import json

with open("old_logs_str.txt", "r", encoding="utf-8") as f:
    old_str = f.read()

new_str = """for i, log in enumerate(current_logs):
        if search_val and search_val.lower() not in log['msg'].lower() and search_val.lower() not in log['level'].lower():
            continue

        color_class = "text-sky-400"
        if log['level'] == 'ERROR': color_class = "text-red-400"
        elif log['level'] == 'WARN': color_class = "text-amber-400"

        # Provide a mocked or real parsed dataset for logs matching the modal design
        row_data = {
            "time": log['time'],
            "protocol": "TCP",
            "data": "1.4 KB",
            "msg": log['msg'],
            "src_ip": "127.0.0.1",
            "src_port": "Random",
            "dst_ip": "127.0.0.1",
            "dst_port": "80",
            "src_mac": "00:15:5d:0a:c0:3d",
            "dst_mac": "a4:b0:cb:11:22:33",
            "src_fqdn": "localhost"
        }

        log_elements.append(
            html.Div(
                id={"type": "conn-row", "index": json.dumps(row_data)}, n_clicks=0,
                className="flex py-1.5 border-b border-slate-800/50 hover:bg-slate-800/40 transition-colors cursor-pointer group", children=[
                html.Span(log['time'], className="w-24 shrink-0 text-slate-500 font-mono group-hover:text-slate-400 transition-colors"),
                html.Span(f"[{log['level']}]", className=f"w-20 shrink-0 font-bold {color_class} font-mono"),
                html.Span(log['msg'], className="flex-1 text-slate-300 group-hover:text-slate-200 transition-colors")
            ])
        )

    """

with open("monitor_new.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(old_str, new_str)

with open("monitor_new.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Logs loop replaced!")
