import re

with open('monitor_new.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_cb = '''@app.callback(
    Output('detail-modal', 'className'),
    Output('modal-content', 'children'),
    Input({'type': 'conn-row', 'index': dash.ALL}, 'n_clicks'),
    Input('close-modal-btn', 'n_clicks'),
    Input('modal-bg', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_modal(row_clicks, close_click, bg_click):'''

new_cb = '''@app.callback(
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
def open_modal(row_clicks):'''

text = text.replace(old_cb, new_cb)

old_logic = '''    trigger = ctx.triggered[0]['prop_id']

    # If close button or background clicked
    if 'close-modal-btn' in trigger or 'modal-bg' in trigger:
        return "hidden fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", ""

    if 'conn-row' in trigger:
        # Check if any row was actually clicked (n_clicks > 0)
        if not any(clicks and clicks > 0 for clicks in row_clicks):
             raise dash.exceptions.PreventUpdate

        # Find which row was clicked'''

new_logic = '''    trigger = ctx.triggered[0]['prop_id']

    if 'conn-row' in trigger:
        # Check if any row was actually clicked (n_clicks > 0)
        if not any(clicks and clicks > 0 for clicks in row_clicks):
             raise dash.exceptions.PreventUpdate

        # Find which row was clicked'''

text = text.replace(old_logic, new_logic)

with open('monitor_new.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed modal callbacks")
