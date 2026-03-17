import dash
from dash import dcc, html, Output, Input
app = dash.Dash(__name__)
app.layout = html.Div([html.Div(id='a'), html.Div(id='b'), html.Div(id='c'), dcc.Location(id='url')])
@app.callback(
    Output('a', 'children'), Output('b', 'className'), Output('c', 'className'),
    Input('url', 'pathname')
)
def cb(p):
    return 'a', 'b', 'c'

if __name__ == '__main__':
    app.run(debug=False, port=8051)
