
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import threading

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    html.Button("Export", id="btn", n_clicks=0),
    dcc.Download(id="download")
])

@app.callback(
    Output("download", "data"),
    Input("btn", "n_clicks"),
    prevent_initial_call=True
)
def export(n):
    return dcc.send_file("network_traffic_log.csv")

def test():
    import time
    time.sleep(2)
    # simulate with dash test client if possible, or just open browser
    import os
    os._exit(0)

threading.Thread(target=test).start()
print("Running dash")
app.run(port=8060, host="127.0.0.1")

