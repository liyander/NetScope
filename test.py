
import json
try:
    trigger = """{"index":"{\"time\":\"2026/03/17 11:00:00\"}","type":"conn-row"}.n_clicks"""
    prop_dict = json.loads(trigger.split(".")[0])
    row_data = json.loads(prop_dict["index"])
    print("OK", row_data)
except Exception as e:
    print("Error:", e)

