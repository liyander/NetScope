import re

with open('monitor_new.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r"@app\.callback\(\s*Output\('detail-modal', 'className'\),\s*Output\('modal-content', 'children'\),\s*Input\(\{'type': 'conn-row', 'index': dash\.ALL\}, 'n_clicks'\),\s*Input\('close-modal-btn', 'n_clicks'\),\s*Input\('modal-bg', 'n_clicks'\),\s*prevent_initial_call=True\s*\)\s*def toggle_modal\(row_clicks, close_click, bg_click\):\s*ctx = dash\.callback_context\s*if not ctx\.triggered:\s*raise dash\.exceptions\.PreventUpdate\s*trigger = ctx\.triggered\[0\]\['prop_id'\]\s*# If close button or background clicked\s*if 'close-modal-btn' in trigger or 'modal-bg' in trigger:\s*return \"hidden fixed inset-0 z-\[100\] items-center justify-center bg-black/60 backdrop-blur-sm\", \"\"\s*if 'conn-row' in trigger:",
    '''@app.callback(
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
def toggle_modal(row_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]['prop_id']

    if 'conn-row' in trigger:''',
    text,
    flags=re.MULTILINE
)

with open('monitor_new.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("done")
