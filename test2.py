
import json
import dash
import click
trigger = "{\"index\":\"{\\\"time\\\":\\\"2026/03/17 11:00\\\",\\\"msg\\\":\\\"Status...\"}\",\"type\":\"conn-row\"}.n_clicks"
parts = trigger.split(".")[0]
print(json.loads(parts))

