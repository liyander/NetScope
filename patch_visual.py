import re
with open('monitor_new.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(
    r'laddr = f"\{c\.laddr\.ip\}"',
    r'laddr = f"{get_hostname(c.laddr.ip)}"',
    text
)
text = re.sub(
    r'raddr_ip = f"\{c\.raddr\.ip\}"',
    r'raddr_ip = f"{get_hostname(c.raddr.ip)}"',
    text
)
with open('monitor_new.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Regex replace Done")
