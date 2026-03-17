with open('monitor_new.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''              html.Button("Export Data", id="btn-export", n_clicks=0, className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium transition-colors text-white shadow-sm border-0 cursor-pointer"),
              dcc.Download(id="download-data")
        html.Main(id='page-content', className="flex-1 w-full mt-24 pb-12"),'''

replacement = '''              html.Button("Export Data", id="btn-export", n_clicks=0, className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium transition-colors text-white shadow-sm border-0 cursor-pointer"),
              dcc.Download(id="download-data")
        ])
    ]),
    html.Main(id='page-content', className="flex-1 w-full mt-24 pb-12"),'''

text = text.replace(target, replacement)

with open('monitor_new.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Syntax fixed")
