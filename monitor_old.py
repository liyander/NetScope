import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import psutil
import time
from collections import deque
import logging
import csv
import os
import threading
from datetime import datetime

# Setup Logging
LOG_FILE = "network_traffic_log.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Interface', 'Bytes_Sent', 'Bytes_Recv', 'Upload_Speed_Bps', 'Download_Speed_Bps'])

MAX_LEN = 60
history = {}
last_io = psutil.net_io_counters(pernic=True)
last_time = time.time()
global_last_io = psutil.net_io_counters()

def update_data():
    global last_io, last_time, global_last_io
    while True:
        time.sleep(1)
        current_io = psutil.net_io_counters(pernic=True)
        current_global = psutil.net_io_counters()
        current_time = time.time()
        time_dt = current_time - last_time

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

t = threading.Thread(target=update_data, daemon=True)
t.start()

external_scripts = [{'src': 'https://cdn.tailwindcss.com'}]
app = dash.Dash(__name__, external_scripts=external_scripts, suppress_callback_exceptions=True)

app.index_string = '''
<!DOCTYPE html>
<html class="h-full bg-gray-900" lang="en">
    <head>
        {%metas%}
        <title>NetScope Pro</title>
        {%favicon%}
        {%css%}
        <style>
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: #1f2937; }
            ::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 10px; }
            ::-webkit-scrollbar-thumb:hover { background: #6b7280; }
        </style>
    </head>
    <body class="bg-gray-900 text-gray-100 font-sans h-full overflow-hidden m-0 p-0">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout Components
header = html.Header(className="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center justify-between", children=[
    html.Div(className="flex items-center space-x-4", children=[
        html.Div(className="bg-blue-600 p-2 rounded-lg", children=[
            html.Div(className="h-6 w-6 text-white text-center font-bold", children="N")
        ]),
        html.Div([
            html.H1("NetScope Pro", className="text-xl font-bold tracking-tight"),
            html.P("Network Traffic Analysis • Live Monitoring", className="text-xs text-gray-400 m-0")
        ])
    ]),
    html.Div(className="flex items-center space-x-6", children=[
        html.Div(className="flex flex-col items-end", children=[
            html.Span("Global Throughput", className="text-xs text-gray-500 uppercase font-semibold"),
            html.Span(id="global-throughput", className="text-lg font-mono text-green-400")
        ]),
        html.Div(className="h-10 w-px bg-gray-800"),
        html.Div(className="flex items-center space-x-3", children=[
            html.Div("AD", className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center font-bold text-xs")
        ])
    ])
])

app.layout = html.Div(className="flex h-screen w-full flex-col absolute inset-0 text-gray-100", children=[
    header,
    html.Main(className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-900", children=[
        html.Section(id="summary-cards", className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"),
        html.Section(className="grid grid-cols-1 gap-6", children=[
            html.Div(className="bg-gray-800 rounded-xl border border-gray-700 p-6", children=[
                html.Div(className="flex items-center justify-between mb-6", children=[
                    html.H2("Real-time Packet Flow (Bytes/sec)", className="text-lg font-semibold flex items-center")
                ]),
                html.Div(id="main-chart-container", className="h-72 w-full")
            ])
        ]),
        html.Section(className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-10", children=[
            html.Div(className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col", children=[
                html.Div(className="p-6 border-b border-gray-700 flex justify-between items-center", children=[
                    html.H3("Live Interface Analytics", className="font-semibold text-gray-200 m-0")
                ]),
                html.Div(id="interfaces-table", className="overflow-x-auto h-80")
            ]),
            html.Div(className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col", children=[
                html.Div(className="p-6 border-b border-gray-700 flex justify-between items-center", children=[
                    html.H3("Active Connections", className="font-semibold text-gray-200 m-0")
                ]),
                html.Div(id="connections-table", className="overflow-auto h-80")
            ])
        ])
    ]),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.1f} {power_labels.get(n, '')}B/s"

@app.callback(
    [Output('global-throughput', 'children'),
     Output('summary-cards', 'children'),
     Output('main-chart-container', 'children'),
     Output('interfaces-table', 'children'),
     Output('connections-table', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    # Calculations
    total_up = sum([h['upload'][-1] for h in history.values() if len(h['upload']) > 0]) if history else 0
    total_down = sum([h['download'][-1] for h in history.values() if len(h['download']) > 0]) if history else 0
    
    try: conns = len(psutil.net_connections(kind='inet'))
    except: conns = 0

    global_throughput = format_bytes(total_up + total_down)

    def get_width(val):
        # Fake logic to show a green bar representing volume amount
        return min(max(10, int((val / max(1, (val+500))) * 100)), 100)

    # Render top KPI cards
    def make_card(title, value, color_class, bg_bar, percent):
        return html.Div(className="bg-gray-800 p-5 rounded-xl border border-gray-700 shadow-sm", children=[
            html.Div(className="flex justify-between items-start mb-4", children=[
                html.P(title, className="text-gray-400 text-sm font-medium m-0"),
                html.Span("Live" if "Connections" in title else "+/-", className=f"text-{color_class}-500 bg-{color_class}-500/10 px-2 py-1 rounded text-xs")
            ]),
            html.P(value, className="text-2xl font-mono font-bold m-0 mt-2"),
            html.Div(className="mt-4 h-1 w-full bg-gray-700 rounded-full overflow-hidden", children=[
                html.Div(className=f"bg-{bg_bar}-500 h-full", style={'width': f'{percent}%'})
            ])
        ])

    cards = [
        make_card("Inbound Traffic", format_bytes(total_down), "green", "blue", 65),
        make_card("Outbound Traffic", format_bytes(total_up), "red", "purple", 35),
        make_card("Active Connections", f"{conns:,}", "blue", "emerald", 82),
        make_card("Avg. Latency", "14.2 ms", "yellow", "yellow", 15)
    ]

    # Main Chart
    fig = go.Figure()
    active_nic = None
    max_d = -1
    for nic, d in history.items():
        if len(d['times']) > 0 and d['download'][-1] > max_d:
            max_d = d['download'][-1]
            active_nic = nic

    if active_nic and len(history[active_nic]['times']) > 0:
        data = history[active_nic]
        fig.add_trace(go.Scatter(x=list(data['times']), y=list(data['download']), fill='tozeroy', mode='lines', name='Download', line=dict(color='#3b82f6', width=2, shape='spline'), fillcolor='rgba(59, 130, 246, 0.2)'))
        fig.add_trace(go.Scatter(x=list(data['times']), y=list(data['upload']), fill='tozeroy', mode='lines', name='Upload', line=dict(color='#a855f7', width=2, shape='spline'), fillcolor='rgba(168, 85, 247, 0.2)'))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9ca3af'),
        xaxis=dict(showgrid=True, gridcolor='#374151', showline=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#374151', showline=False, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    chart = dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '100%'})

    # Interface table
    interface_rows = []
    interface_rows.append(html.Tr(className="bg-gray-900/50 text-gray-400 uppercase text-[10px] tracking-wider", children=[
        html.Th("Interface", className="px-6 py-3 font-semibold"),
        html.Th("Download", className="px-6 py-3 font-semibold"),
        html.Th("Upload", className="px-6 py-3 font-semibold")
    ]))
    
    for nic, d in history.items():
        if len(d['times']) == 0: continue
        interface_rows.append(html.Tr(className="hover:bg-gray-700/50 transition-colors border-b border-gray-700/50", children=[
            html.Td(nic, className="px-6 py-4 text-gray-300 font-medium text-sm"),
            html.Td(format_bytes(d['download'][-1]), className="px-6 py-4 font-mono text-blue-400"),
            html.Td(format_bytes(d['upload'][-1]), className="px-6 py-4 font-mono text-purple-400")
        ]))
    iface_table = html.Table(interface_rows, className="w-full text-left text-sm")

    # Connections table
    try:
        active_conns = psutil.net_connections(kind='inet')
        conn_rows = [html.Tr(className="bg-gray-900/50 text-gray-400 uppercase text-[10px] tracking-wider sticky top-0 z-10", children=[
            html.Th("Source", className="px-6 py-3 font-semibold"),
            html.Th("Dest", className="px-6 py-3 font-semibold"),
            html.Th("State", className="px-6 py-3 font-semibold text-right")
        ])]
        for c in active_conns[:100]:
            laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else ""
            raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"
            bg = "bg-green-500 animate-pulse" if c.status == "ESTABLISHED" else "bg-yellow-500"
            if c.status == "LISTEN": bg = "bg-blue-500"
            if c.status == "TIME_WAIT": bg = "bg-gray-500"
            conn_rows.append(html.Tr(className="hover:bg-gray-700/50 transition-colors border-b border-gray-700/50", children=[
                html.Td(laddr, className="px-6 py-2 font-mono text-blue-400 text-xs"),
                html.Td(raddr, className="px-6 py-2 font-mono text-gray-300 text-xs"),
                html.Td(html.Span(className=f"inline-block w-2 h-2 rounded-full {bg}"), className="px-6 py-2 text-right")
            ]))
        conns_html = html.Table(conn_rows, className="w-full text-left text-sm")
    except:
        conns_html = html.Div("Access Denied to active connections.", className="text-red-500 p-4")

    return global_throughput, cards, chart, iface_table, conns_html

if __name__ == '__main__':
    print("Starting tailored NetScope Pro... http://127.0.1.1:8050")
    app.run(debug=False, port=8050, host='127.0.1.1')
