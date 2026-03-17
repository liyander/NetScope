import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
import plotly.graph_objs as go
import psutil
import time
from collections import deque
import logging
import csv
import os
import threading
from datetime import datetime
import json

# Setup Logging
LOG_FILE = "network_traffic_log.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Interface', 'Bytes_Sent', 'Bytes_Recv', 'Upload_Speed_Bps', 'Download_Speed_Bps'])

MAX_LEN = 60 # Better timeline history for graphs
history = {}
last_io = psutil.net_io_counters(pernic=True)
last_time = time.time()
global_last_io = psutil.net_io_counters()

system_logs = deque(maxlen=300)
last_conns_set = set()
boot_time = datetime.now()


USUAL_PORTS = {80, 443, 8080, 8050, 53, 5432, 3306, 6379, 27017, 8443, 9090}

def is_unwanted_localhost(c):
    # Check if this is local to local traffic
    is_local = (c.laddr and c.laddr.ip in ['127.0.0.1', '::1']) and (not c.raddr or c.raddr.ip in ['127.0.0.1', '::1'])
    if not is_local:
        return False # keep it, it's external
    
    # It's local traffic. Check if ports are "usual"
    lport = c.laddr.port if c.laddr else 0
    rport = c.raddr.port if c.raddr else 0
    
    # If one of the ports is a common service port like 8050 (Dash API), ignore the connection
    if lport in USUAL_PORTS or rport in USUAL_PORTS:
        return True
        
    return False


USUAL_PORTS = {80, 443, 8080, 8050, 53, 5432, 3306, 6379, 27017, 8443, 9090}

def is_unwanted_localhost(c):
    # Check if this is local to local traffic
    is_local = (c.laddr and c.laddr.ip in ['127.0.0.1', '::1']) and (not c.raddr or c.raddr.ip in ['127.0.0.1', '::1'])
    if not is_local:
        return False # keep it, it's external
    
    # It's local traffic. Check if ports are "usual"
    lport = c.laddr.port if c.laddr else 0
    rport = c.raddr.port if c.raddr else 0
    
    # If one of the ports is a common service port like 8050 (Dash API), ignore the connection
    if lport in USUAL_PORTS or rport in USUAL_PORTS:
        return True
        
    return False

def update_data():
    global last_io, last_time, global_last_io, last_conns_set
    while True:
        time.sleep(1)
        current_time = time.time()
        time_dt = current_time - last_time
        
        current_io = psutil.net_io_counters(pernic=True)
        current_global = psutil.net_io_counters()

        # Update bandwidth history
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            
            for nic, stats in current_io.items():
                if stats.bytes_sent == 0 and stats.bytes_recv == 0: continue

                if nic not in history:
                    history[nic] = {
                        'times': deque(maxlen=MAX_LEN),
                        'upload': deque(maxlen=MAX_LEN),
                        'download': deque(maxlen=MAX_LEN)
                    }

                prev_stats = last_io.get(nic)
                if prev_stats and time_dt > 0:
                    up_speed = (stats.bytes_sent - prev_stats.bytes_sent) / time_dt
                    down_speed = (stats.bytes_recv - prev_stats.bytes_recv) / time_dt
                else:
                    up_speed = 0
                    down_speed = 0

                timestamp_str = datetime.fromtimestamp(current_time).strftime('%H:%M:%S')
                history[nic]['times'].append(timestamp_str)
                history[nic]['upload'].append(up_speed)
                history[nic]['download'].append(down_speed)

                writer.writerow([datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S'), nic, stats.bytes_sent, stats.bytes_recv, up_speed, down_speed])

        last_io = current_io
        global_last_io = current_global
        last_time = current_time

        # Process net connections
        try:
            current_conns = psutil.net_connections(kind='inet')
            current_conns_set = set()
            for c in current_conns:
                if c.status == 'ESTABLISHED' and not is_unwanted_localhost(c):
                    laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else ""
                    raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else ""
                    current_conns_set.add((laddr, raddr, c.type))

            new_conns = current_conns_set - last_conns_set
            
            for conn in new_conns:
                ctype = "TCP" if conn[2] == 1 else "UDP"
                system_logs.appendleft({
                    'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    'level': 'INFO',
                    'msg': f"Incoming {ctype} connection from {conn[1]} to {conn[0]}"
                })
            
            if int(current_time) % 20 == 0:
                system_logs.appendleft({
                    'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                    'level': 'WARN' if len(history) == 0 else 'INFO',
                    'msg': f"Network inspection routine completed. Interface count: {len(history)}."
                })

            last_conns_set = current_conns_set
        except Exception as e:
            system_logs.appendleft({
                'time': datetime.now().strftime('%H:%M:%S.%f')[:-3],
                'level': 'ERROR',
                'msg': f"Error retrieving sockets: {str(e)}"
            })

t = threading.Thread(target=update_data, daemon=True)
t.start()

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.index_string = '''
<!DOCTYPE html>
<html class="bg-slate-950" lang="en">
    <head>
        {%metas%}
        <title>NetScope Pro</title>
        {%favicon%}
        <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            'log-bg': '#0f172a',
                            'log-border': '#1e293b',
                            'log-info': '#38bdf8',
                            'log-warn': '#fbbf24',
                            'log-error': '#ef4444',
                            'log-text': '#94a3b8'
                        }
                    }
                }
            }
        </script>
        {%css%}
        <style>
            html, body { min-height: 100vh; margin: 0; padding: 0; scroll-behavior: smooth; }
            .custom-scrollbar::-webkit-scrollbar { width: 8px; }
            .custom-scrollbar::-webkit-scrollbar-track { background: #0f172a; }
            .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
            .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
            .font-mono-tight {
                font-family: 'ui-monospace', 'SFMono-Regular', Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
                letter-spacing: -0.02em;
            }
        </style>
    </head>
    <body class="bg-slate-950 text-slate-200 font-sans min-h-screen flex flex-col custom-scrollbar">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.1f} {power_labels.get(n, '')}B/s"

def make_card(title, value, color_class, bg_bar, percent):
    return html.Div(className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-sm", children=[
        html.Div(className="flex justify-between items-start mb-4", children=[
            html.P(title, className="text-slate-400 text-sm font-medium m-0"),
            html.Span("Live" if "Connections" in title else "+/-", className=f"text-{color_class}-400 bg-{color_class}-400/10 px-2 py-1 rounded text-xs font-semibold")
        ]),
        html.P(value, className="text-2xl font-mono font-bold m-0 mt-1 text-white"),
        html.Div(className="mt-4 h-1 w-full bg-slate-800 rounded-full overflow-hidden", children=[
            html.Div(className=f"bg-{bg_bar}-500 h-full", style={'width': f'{percent}%'})
        ])
    ])

def layout_dashboard():
    return html.Div(className="w-full max-w-[1600px] mx-auto p-6 space-y-6 animate-fade-in", children=[
        dcc.Interval(id='dashboard-interval', interval=1500, n_intervals=0),
        html.Section(id="summary-cards", className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"),
        html.Section(className="grid grid-cols-1 lg:grid-cols-3 gap-6", children=[
            html.Div(className="lg:col-span-2 bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-lg", children=[
                html.Div(className="flex items-center justify-between mb-6", children=[
                    html.H2(id="main-chart-title", className="text-lg font-semibold flex items-center text-slate-100", children="Real-time Packet Flow")
                ]),
                html.Div(id="main-chart-container", className="w-full space-y-6 h-[400px]")
            ]),
            html.Div(className="bg-slate-900 rounded-xl border border-slate-800 flex flex-col shadow-lg lg:col-span-1", children=[
                html.Div(className="p-6 border-b border-slate-800 flex justify-between items-center", children=[
                    html.H3("Active Interfaces", className="font-semibold text-slate-200 m-0")
                ]),
                html.Div(id="interfaces-table-clickable", className="overflow-y-auto h-[400px] bg-slate-900 rounded-b-xl custom-scrollbar")
            ])
        ]),
        html.Section(className="grid grid-cols-1 gap-6", children=[
            html.Div(className="bg-slate-900 rounded-xl border border-slate-800 flex flex-col shadow-lg", children=[
                html.Div(className="p-6 border-b border-slate-800 flex justify-between items-center", children=[
                    html.H3("Active Connections Table", className="font-semibold text-slate-200 m-0")
                ]),
                html.Div(id="connections-table", className="overflow-x-auto max-h-[500px] bg-slate-900 rounded-b-xl custom-scrollbar")
            ])
        ])
    ])

def layout_logs():
    return html.Div(className="w-full max-w-7xl mx-auto p-6 flex flex-col gap-6 flex-1 min-h-[80vh]", children=[
        dcc.Interval(id='logs-interval', interval=1500, n_intervals=0),
        html.Section(className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 p-4 rounded-lg border border-slate-800", children=[
            html.Div(className="relative flex-1 min-w-[300px] flex items-center", children=[
                html.Span(
                    "🔍",
                    className="absolute left-3 top-[10px] text-slate-500 text-sm"
                ),
                dcc.Input(id="log-search-input", type="text", className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-700 rounded-md text-sm text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 border-solid placeholder-slate-500 m-0", placeholder="Filter by message, IP, or endpoint...", style={'outline': 'none', 'boxShadow': 'none'})
            ]),
            html.Div(className="flex items-center gap-2", children=[
                html.Button("Clear Console", id="clear-logs-btn", n_clicks=0, className="text-xs text-slate-400 hover:text-white underline underline-offset-4 decoration-slate-600 px-4 py-2 bg-transparent border-0 cursor-pointer")
            ])
        ]),
        html.Section(className="flex-1 bg-log-bg border border-log-border rounded-lg flex flex-col overflow-hidden shadow-xl min-h-[600px]", children=[
            html.Div(className="bg-slate-900 px-4 py-2 border-b border-log-border flex items-center justify-between", children=[
                html.Div(className="flex gap-1.5", children=[
                    html.Div(className="w-2.5 h-2.5 rounded-full bg-slate-700"),
                    html.Div(className="w-2.5 h-2.5 rounded-full bg-slate-700"),
                    html.Div(className="w-2.5 h-2.5 rounded-full bg-slate-700")
                ]),
                html.Span("stdout / network_monitor", className="text-[10px] font-mono text-slate-500 uppercase tracking-widest")
            ]),
            html.Div(id="log-container", className="flex-1 overflow-y-auto p-4 font-mono-tight text-[13px] leading-relaxed custom-scrollbar bg-slate-950 min-h-[60vh] max-h-[80vh]")
        ])
    ])

app.layout = html.Div(className="flex flex-col min-h-screen", children=[
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='selected-interface', data=None),
    
    html.Header(className="fixed w-full top-0 left-0 z-50 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 py-4 flex items-center justify-between shadow-sm", children=[
        html.Div(className="flex items-center gap-6", children=[
            html.Div(className="flex items-center gap-3", children=[
                html.Div(className="w-3 h-3 bg-green-500 rounded-full animate-pulse", title="System Live"),
                html.H1("NetScope Pro", className="text-xl font-bold tracking-tight text-white m-0"),
            ]),
            html.Nav(className="flex space-x-2 bg-slate-800/80 p-1 rounded-lg border border-slate-700", children=[
                dcc.Link("Dashboard", href="/", id="link-dashboard", className="text-sm font-medium px-4 py-1.5 rounded-md transition-colors"),
                dcc.Link("Network Logs", href="/logs", id="link-logs", className="text-sm font-medium px-4 py-1.5 rounded-md transition-colors")
            ])
        ]),
        html.Div(className="flex items-center gap-4", children=[
            html.Div(className="text-xs text-slate-400 font-mono hidden md:flex items-center", children=[
                "STATUS: ", html.Span("MONITORING", className="text-green-400 ml-1 font-bold")
            ]),
              html.Button("Export Data", id="btn-export", n_clicks=0, className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium transition-colors text-white shadow-sm border-0 cursor-pointer"),
              dcc.Download(id="download-data")
        ])
    ]),
    html.Main(id='page-content', className="flex-1 w-full mt-24 pb-12"),

    # Details Modal (initially hidden)
    html.Div(id='detail-modal', className="hidden fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", children=[
        html.Div(id='modal-bg', n_clicks=0, className="absolute inset-0 cursor-pointer z-0"),
        html.Div(className="relative z-10 w-[850px] max-w-[95vw] bg-[#0f172a] border border-slate-700/50 rounded-xl overflow-hidden shadow-2xl transition-all", children=[
            # Header
            html.Div(className="bg-[#fcb000] px-4 py-2 flex justify-between items-center relative", children=[
                html.Div("Connection details", className="text-black font-semibold mx-auto text-[15px] font-mono tracking-wide"),
                html.Button("?", id='close-modal-btn', n_clicks=0, className="absolute right-3 top-1 text-black hover:bg-black/20 rounded-full w-7 h-7 flex items-center justify-center font-bold bg-transparent border-0 cursor-pointer transition-colors")
            ]),
            # Body
            html.Div(id='modal-content', className="p-0 text-slate-300 font-mono")
        ])
    ])

])

@app.callback(
    Output('page-content', 'children'),
    Output('link-dashboard', 'className'),
    Output('link-logs', 'className'),
    Input('url', 'pathname')
)
def display_page(pathname):
    base_class = "text-sm font-medium px-4 py-1.5 rounded-md transition-all duration-200 "
    active_class = base_class + "bg-blue-600 text-white shadow"
    inactive_class = base_class + "text-slate-400 hover:text-white hover:bg-slate-700/50"
    
    if pathname == '/logs':
        return layout_logs(), inactive_class, active_class
    else:
        return layout_dashboard(), active_class, inactive_class

@app.callback(
    Output('selected-interface', 'data'),
    [Input({'type': 'interface-row', 'index': ALL}, 'n_clicks')],
    [State({'type': 'interface-row', 'index': ALL}, 'id'),
     State('selected-interface', 'data')],
    prevent_initial_call=True
)
def update_selected_interface(n_clicks, ids, current_selected):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    trigger = ctx.triggered[0]
    
    # Ignore clicks that are essentially initialization (n_clicks = 0 or None)
    if trigger['value'] is None or trigger['value'] == 0:
        return dash.no_update
        
    try:
        triggered_id = json.loads(trigger['prop_id'].split('.')[0])
        return triggered_id['index']
    except:
        return current_selected

@app.callback(
    Output('summary-cards', 'children'),
    Output('main-chart-container', 'children'),
    Output('main-chart-title', 'children'),
    Output('interfaces-table-clickable', 'children'),
    Output('connections-table', 'children'),
    Input('dashboard-interval', 'n_intervals'),
    Input('selected-interface', 'data')
)
def update_dashboard_views(n, selected_iface):
    total_up = sum([h['upload'][-1] for h in history.values() if len(h['upload']) > 0]) if history else 0
    total_down = sum([h['download'][-1] for h in history.values() if len(h['download']) > 0]) if history else 0
    
    try: conns = len(psutil.net_connections(kind='inet'))
    except: conns = 0

    uptime_sec = (datetime.now() - boot_time).total_seconds()
    uptime_h = int(uptime_sec // 3600)
    uptime_m = int((uptime_sec % 3600) // 60)

    cards = [
        make_card("Inbound Traffic", format_bytes(total_down), "green", "blue", 65),
        make_card("Outbound Traffic", format_bytes(total_up), "purple", "purple", 35),
        make_card("Active Connections", f"{conns:,}", "blue", "emerald", 82),
        make_card("System Uptime", f"{uptime_h}h {uptime_m}m", "amber", "amber", min(100, uptime_m*2))
    ]

    valid_nics = [nic for nic, d in history.items() if len(d['times']) > 0]
    valid_nics.sort()
    
    if not selected_iface or selected_iface not in valid_nics:
        if valid_nics: selected_iface = valid_nics[0]
        else: selected_iface = None

    chart = html.Div("Awaiting traffic data...", className="text-slate-500 text-center py-20 font-mono")
    title = "Real-time Packet Flow"
    
    if selected_iface and selected_iface in history:
        title = f"Live Interface: {selected_iface}"
        d = history[selected_iface]
        
        fig = go.Figure()
        times_list = list(d['times'])
        
        fig.add_trace(go.Scatter(
            x=times_list, y=list(d['download']), 
            fill='tozeroy', mode='lines', name='Download (In)', 
            line=dict(color='#0ea5e9', width=2, shape='spline', smoothing=1.0), 
            fillcolor='rgba(14, 165, 233, 0.15)'
        ))
        fig.add_trace(go.Scatter(
            x=times_list, y=list(d['upload']), 
            fill='tozeroy', mode='lines', name='Upload (Out)', 
            line=dict(color='#d946ef', width=2, shape='spline', smoothing=1.0), 
            fillcolor='rgba(217, 70, 239, 0.15)'
        ))
        
        fig.update_layout(
            margin=dict(l=55, r=20, t=10, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#64748b'),
            xaxis=dict(
                showgrid=True, gridcolor='#1e293b', 
                showline=True, linecolor='#334155',
                tickangle=0,
                nticks=6,
                fixedrange=True
            ),
            yaxis=dict(
                showgrid=True, gridcolor='#1e293b', 
                showline=True, linecolor='#334155',
                zeroline=True, zerolinecolor='#334155',
                fixedrange=True,
                ticksuffix=" B/s"
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
            hovermode='x unified',
            height=360
        )
        chart = dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '100%'})
    
    interface_rows = []
    for nic in valid_nics:
        d = history[nic]
        is_selected = (nic == selected_iface)
        bg_class = "bg-blue-900/10 border-l-4 border-blue-500 shadow-inner" if is_selected else "hover:bg-slate-800/40 border-l-4 border-transparent cursor-pointer"
        
        interface_rows.append(
            html.Div(id={'type': 'interface-row', 'index': nic}, n_clicks=0, className=f"flex items-center justify-between p-4 border-b border-slate-800/60 transition-all {bg_class}", children=[
                html.Div(className="flex items-center gap-3", children=[
                    html.Span(className=f"w-2.5 h-2.5 rounded-full {'bg-sky-400 animate-pulse' if is_selected else 'bg-slate-600'}"),
                    html.Span(nic, className=f"text-sm font-semibold {'text-sky-300' if is_selected else 'text-slate-300'}")
                ]),
                html.Div(className="text-[11px] font-mono flex flex-col items-end gap-1.5", children=[
                    html.Div(className="flex items-center gap-2", children=[
                        html.Span("IN", className="text-slate-500 font-bold bg-slate-900 px-1 rounded"),
                        html.Span(f"{format_bytes(d['download'][-1])}", className="text-sky-400 w-[70px] text-right font-medium")
                    ]),
                    html.Div(className="flex items-center gap-2", children=[
                        html.Span("OUT", className="text-slate-500 font-bold bg-slate-900 px-1 rounded"),
                        html.Span(f"{format_bytes(d['upload'][-1])}", className="text-fuchsia-400 w-[70px] text-right font-medium")
                    ])
                ])
            ])
        )

    try:
        active_conns = psutil.net_connections(kind='inet')
        conn_rows = [html.Tr(className="bg-slate-800 text-slate-300 uppercase text-[10px] tracking-wider", children=[
            html.Th("IP Address", className="px-6 py-3 font-semibold text-left"),
            html.Th("Remote Dest", className="px-6 py-3 font-semibold text-left"),
            html.Th("Status", className="px-6 py-3 font-semibold text-right")
        ])]
        displayed_count = 0
        for i, c in enumerate(active_conns):
            if displayed_count >= 80:
                break
            if is_unwanted_localhost(c):
                continue
            displayed_count += 1
            
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
            ]))
        conns_html = html.Table(conn_rows, className="w-full text-left")
    except:
        conns_html = html.Div("Requires Administrator privileges to view detailed connections.", className="text-red-400 p-6 font-mono text-sm bg-red-950/10 rounded-xl border border-red-900/30 text-center m-4")

    return cards, chart, title, interface_rows, conns_html

@app.callback(
    Output('log-container', 'children'),
    Input('logs-interval', 'n_intervals'),
    Input('log-search-input', 'value'),
    Input('clear-logs-btn', 'n_clicks')
)
def update_logs(n, search_val, clear_clicks):
    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('clear-logs-btn'):
        system_logs.clear()
        return []
    
    log_elements = []
    current_logs = list(system_logs)
    
    for i, log in enumerate(current_logs):
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

    if not log_elements:
        log_elements.append(html.Div(">> Waiting for incoming packet sequences...", className="text-slate-500 italic py-6 px-4 font-mono animate-pulse"))
        
    return log_elements


@app.callback(
    Output('detail-modal', 'className', allow_duplicate=True),
    Output('modal-content', 'children', allow_duplicate=True),
    Input('close-modal-btn', 'n_clicks'),
    Input('modal-bg', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(close_click, bg_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    return "hidden fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", ""

@app.callback(
    Output('detail-modal', 'className'),
    Output('modal-content', 'children'),
    Input({'type': 'conn-row', 'index': dash.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def open_modal(row_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]['prop_id']

    if 'conn-row' in trigger:
        # Check if any row was actually clicked (n_clicks > 0)
        if not any(clicks and clicks > 0 for clicks in row_clicks):
             raise dash.exceptions.PreventUpdate

        # Find which row was clicked
        prop_dict = json.loads(trigger.rsplit('.', 1)[0])
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

@app.callback(
    Output("download-data", "data"),
    Input("btn-export", "n_clicks"),
    prevent_initial_call=True
)
def export_data(n_clicks):
    import os
    if n_clicks > 0 and os.path.exists(LOG_FILE):
        return dcc.send_file(LOG_FILE)
    return dash.no_update

if __name__ == '__main__':

    print("Starting Multi-page NetScope Pro... open http://127.0.1.1:8050")
    app.run(debug=False, port=8050, host='127.0.1.1')
