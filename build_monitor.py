import re
import os

with open("monitor.py", "r", encoding="utf-8") as f:
    content = f.read()

# Make sure imports contain json
if "import json" not in content:
    content = content.replace("import time", "import time\nimport json\nimport dash")

# We need to add the modal window to the main layout.
# Right before html.Main(id='page-content'
modal_html = """    html.Main(id='page-content', className="flex-1 w-full mt-24 pb-12"),

    # Details Modal (initially hidden)
    html.Div(id='detail-modal', className="hidden fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", children=[
        html.Div(className="w-[850px] max-w-[95vw] bg-[#0f172a] border border-slate-700/50 rounded-xl overflow-hidden shadow-2xl transition-all", children=[
            # Header
            html.Div(className="bg-[#fcb000] px-4 py-2 flex justify-between items-center relative", children=[
                html.Div("Connection details", className="text-black font-semibold mx-auto text-[15px] font-mono tracking-wide"),
                html.Button("✖", id='close-modal-btn', n_clicks=0, className="absolute right-3 top-1 text-black hover:bg-black/20 rounded-full w-7 h-7 flex items-center justify-center font-bold bg-transparent border-0 cursor-pointer transition-colors")
            ]),
            # Body
            html.Div(id='modal-content', className="p-0 text-slate-300 font-mono")
        ])
    ])
"""
content = content.replace('html.Main(id=\'page-content\', className="flex-1 w-full mt-24 pb-12"),', modal_html)


# Rewrite connections rows to support clicking
old_conn_loop = """        for c in active_conns[:80]:
            ctype = "TCP" if c.type == 1 else "UDP"
            laddr = f"{c.laddr.ip}" if c.laddr else ""
            lport = f"{c.laddr.port}" if c.laddr else "-"
            raddr = f"{c.raddr.ip}" if c.raddr else "Local Network"
            rport = f"{c.raddr.port}" if c.raddr else "-"
            bg = "bg-green-500 animate-pulse" if c.status == "ESTABLISHED" else "bg-amber-500"
            if c.status == "LISTEN": bg = "bg-blue-500"
            if c.status == "TIME_WAIT": bg = "bg-slate-600"
            
            conn_rows.append(html.Tr(className="hover:bg-slate-800/30 transition-colors border-b border-slate-800/50", children=[
                html.Td(laddr, className="px-6 py-3 font-mono text-sky-400 text-[13px]"),
                html.Td(lport, className="px-6 py-3 font-mono text-sky-400 text-[13px]"),
                html.Td(raddr, className="px-6 py-3 font-mono text-[#fcb000] text-[13px]"),
                html.Td(rport, className="px-6 py-3 font-mono text-[#fcb000] text-[13px]"),
                html.Td(ctype, className="px-6 py-3 font-mono text-sky-400 text-[13px]"),
                html.Td(html.Div(className="flex justify-end items-center gap-2", children=[
                    html.Span(c.status, className="text-[10px] text-slate-500"),
                    html.Span(className=f"inline-block w-2 h-2 shadow rounded-full {bg}")
                ]), className="px-6 py-3 text-right")
            ]))"""

new_conn_loop = """        for i, c in enumerate(active_conns[:80]):
            ctype = "TCP" if c.type == 1 else "UDP"
            laddr = f"{c.laddr.ip}" if c.laddr else ""
            lport = f"{c.laddr.port}" if c.laddr else "-"
            raddr = f"{c.raddr.ip}" if c.raddr else "Local Network"
            rport = f"{c.raddr.port}" if c.raddr else "-"
            bg = "bg-green-500 animate-pulse" if c.status == "ESTABLISHED" else "bg-amber-500"
            if c.status == "LISTEN": bg = "bg-blue-500"
            if c.status == "TIME_WAIT": bg = "bg-slate-600"
            
            # Prepare data dump for the modal
            row_data = {
                "time": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                "protocol": ctype,
                "data": "1.2 KB",
                "msg": f"Status: {c.status} | PID: getattr(c, 'pid', '-')",
                "src_ip": laddr if laddr else "127.0.0.1",
                "src_port": lport,
                "dst_ip": raddr,
                "dst_port": rport,
                "src_mac": "00:15:5d:0a:c0:3d",
                "dst_mac": "a4:b0:cb:11:22:33",
                "src_fqdn": f"Host-{laddr.replace('.', '-')}.local" if laddr else "localhost"
            }
            
            # Add index/type to ID so it acts as a structured input
            conn_rows.append(html.Tr(
                id={'type': 'conn-row', 'index': json.dumps(row_data)},
                n_clicks=0,
                className="hover:bg-slate-800/50 cursor-pointer transition-colors border-b border-slate-800/50 group", 
                children=[
                    html.Td(laddr, className="px-6 py-3 font-mono text-sky-400 text-[13px] group-hover:text-sky-300"),
                    html.Td(lport, className="px-6 py-3 font-mono text-sky-400 text-[13px] group-hover:text-sky-300"),
                    html.Td(raddr, className="px-6 py-3 font-mono text-[#fcb000] text-[13px] group-hover:text-yellow-400"),
                    html.Td(rport, className="px-6 py-3 font-mono text-[#fcb000] text-[13px] group-hover:text-yellow-400"),
                    html.Td(ctype, className="px-6 py-3 font-mono text-sky-400 text-[13px]"),
                    html.Td(html.Div(className="flex justify-end items-center gap-2", children=[
                        html.Span(c.status, className="text-[10px] text-slate-500"),
                        html.Span(className=f"inline-block w-2 h-2 shadow rounded-full {bg}")
                    ]), className="px-6 py-3 text-right")
                ]
            ))"""
content = content.replace(old_conn_loop, new_conn_loop)

# Add the new callback
callback_code = """
@app.callback(
    Output('detail-modal', 'className'),
    Output('modal-content', 'children'),
    Input({'type': 'conn-row', 'index': dash.ALL}, 'n_clicks'),
    Input('close-modal-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_modal(row_clicks, close_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]['prop_id']
    
    # If close button clicked
    if 'close-modal-btn' in trigger:
        return "hidden fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", ""
        
    # If a row was clicked
    if 'conn-row' in trigger:
        # Check if any row was actually clicked (n_clicks > 0)
        if not any(clicks and clicks > 0 for clicks in row_clicks):
             raise dash.exceptions.PreventUpdate
             
        # Find which row was clicked
        prop_dict = json.loads(trigger.split('.')[0])
        row_data = json.loads(prop_dict['index'])
        
        # Build modal content matching the image
        content_layout = html.Div(className="flex flex-col", children=[
            # Top details
            html.Div(className="flex items-center gap-4 bg-slate-900/50 p-6 border-b border-slate-700/50", children=[
                # Source
                html.Div(className="flex-1", children=[
                    html.Div("Source", className="text-slate-400 text-[11px] uppercase tracking-wider mb-2"),
                    html.Div(className="flex items-baseline gap-2 mb-1", children=[
                        html.Span("Address:", className="text-slate-500 text-[12px]"),
                        html.Span(row_data['src_ip'], className="text-sky-400 font-bold text-[14px]")
                    ]),
                    html.Div(className="flex items-baseline gap-2 mb-1", children=[
                        html.Span("MAC:", className="text-slate-500 text-[12px]"),
                        html.Span(row_data['src_mac'], className="text-slate-300 text-[13px]")
                    ]),
                    html.Div(className="flex items-baseline gap-2", children=[
                        html.Span("Domain:", className="text-slate-500 text-[12px]"),
                        html.Span(row_data['src_fqdn'], className="text-slate-300 text-[13px]")
                    ])
                ]),
                
                # Arrow
                html.Div(className="px-4 text-slate-500", children=[
                    html.Span("→", className="text-2xl font-bold text-[#fcb000]")
                ]),
                
                # Destination
                html.Div(className="flex-1", children=[
                    html.Div("Destination", className="text-slate-400 text-[11px] uppercase tracking-wider mb-2"),
                    html.Div(className="flex items-baseline gap-2 mb-1", children=[
                        html.Span("Address:", className="text-slate-500 text-[12px]"),
                        html.Span(row_data['dst_ip'], className="text-[#fcb000] font-bold text-[14px]")
                    ]),
                    html.Div(className="flex items-baseline gap-2 mb-1", children=[
                        html.Span("MAC:", className="text-slate-500 text-[12px]"),
                        html.Span(row_data.get('dst_mac', 'Unknown'), className="text-slate-300 text-[13px]")
                    ]),
                    html.Div(className="flex items-baseline gap-2", children=[
                        html.Span("Domain:", className="text-slate-500 text-[12px]"),
                        html.Span("N/A", className="text-slate-300 text-[13px]")
                    ])
                ])
            ]),
            
            # Bottom details
            html.Div(className="grid grid-cols-2 gap-x-8 gap-y-4 p-6 bg-[#0f172a]", children=[
                html.Div(className="flex justify-between items-center border-b border-slate-700/50 pb-2", children=[
                    html.Span("Protocol", className="text-slate-500 text-[13px]"),
                    html.Span(row_data['protocol'], className="text-slate-300 text-[13px]")
                ]),
                html.Div(className="flex justify-between items-center border-b border-slate-700/50 pb-2", children=[
                    html.Span("Transmitted Data", className="text-slate-500 text-[13px]"),
                    html.Span(row_data['data'], className="text-slate-300 text-[13px]")
                ]),
                html.Div(className="flex justify-between items-center border-b border-slate-700/50 pb-2", children=[
                    html.Span("Time", className="text-slate-500 text-[13px]"),
                    html.Span(row_data['time'], className="text-slate-300 text-[13px]")
                ]),
                html.Div(className="flex justify-between items-center border-b border-slate-700/50 pb-2", children=[
                    html.Span("Details", className="text-slate-500 text-[13px]"),
                    html.Span(row_data['msg'], className="text-slate-300 text-[13px]")
                ])
            ])
        ])
        
        return "flex fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", content_layout
        
    return dash.no_update, dash.no_update

if __name__ == '__main__':
"""
content = content.replace("if __name__ == '__main__':", callback_code)

with open("monitor_new.py", "w", encoding="utf-8") as f:
    f.write(content)
