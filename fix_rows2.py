
import re

with open("monitor_new.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r"        for c in active_conns\[:80\]:.*?\]\)\)\)\]\"\"\""  # Oh wait, regex cross line doesn't work like this easily unless re.DOTALL


