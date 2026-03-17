import re

with open("monitor_new.py", "r", encoding="utf-8") as f:
    text = f.read()

new_func = """
    def resolve():
        try:
            name = socket.gethostbyaddr(ip)[0]
            if "1e100.net" in name:
                name = f"Google ({name})"
            elif "amazonaws.com" in name:
                name = f"AWS ({name})"
            elif "edgecast" in name:
                name = f"Edgecast ({name})"
            elif "fastly" in name.lower():
                name = f"Fastly ({name})"
            elif "trafficmanager.net" in name:
                name = f"Azure ({name})"
            elif "apple.com" in name:
                name = f"Apple ({name})"
            elif "cloudfront.net" in name:
                name = f"CloudFront ({name})"
            return name
        except Exception:
            return ip

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(resolve)
        try:
            hostname = future.result(timeout=0.3)
            dns_cache[ip] = hostname
            return hostname
        except Exception:
            dns_cache[ip] = ip
            return ip
"""

# Replace the inner resolve till the end of the function
text = re.sub(
    r'\s+def resolve\(\):.+?return ip\n',
    new_func + "\n",
    text,
    flags=re.DOTALL
)

with open("monitor_new.py", "w", encoding="utf-8") as f:
    f.write(text)
print("done")
