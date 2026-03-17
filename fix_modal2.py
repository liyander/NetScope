
with open("monitor_new.py", "r", encoding="utf-8") as f:
    content = f.read()

modal_html = """    html.Main(id='page-content', className="flex-1 w-full mt-24 pb-12"),

    # Details Modal (initially hidden)
    html.Div(id='detail-modal', className="hidden fixed inset-0 z-[100] items-center justify-center bg-black/60 backdrop-blur-sm", children=[
        html.Div(className="w-[850px] max-w-[95vw] bg-[#0f172a] border border-slate-700/50 rounded-xl overflow-hidden shadow-2xl transition-all", children=[
            # Header
            html.Div(className="bg-[#fcb000] px-4 py-2 flex justify-between items-center relative", children=[
                html.Div("Connection details", className="text-black font-semibold mx-auto text-[15px] font-mono tracking-wide"),
                html.Button("?", id='close-modal-btn', n_clicks=0, className="absolute right-3 top-1 text-black hover:bg-black/20 rounded-full w-7 h-7 flex items-center justify-center font-bold bg-transparent border-0 cursor-pointer transition-colors")
            ]),
            # Body
            html.Div(id='modal-content', className="p-0 text-slate-300 font-mono")
        ])
    ])
"""

content = content.replace("html.Main(id='page-content', className=\"flex-1 w-full mt-24 pb-12\")", modal_html)

with open("monitor_new.py", "w", encoding="utf-8") as f:
    f.write(content)
print("done")

