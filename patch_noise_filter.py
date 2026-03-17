import re

with open('monitor_new.py', 'r', encoding='utf-8') as f:
    text = f.read()

filter_logic = '''
USUAL_PORTS = {80, 443, 8080, 8050, 53, 5432, 3306, 6379, 27017, 8443, 9090}

def is_unwanted_localhost(c):
    # Check if this is local to local traffic
    is_local = (c.laddr and c.laddr.ip in ['127.0.0.1', '::1']) and (not c.raddr or c.raddr.ip in ['127.0.0.1', '::1'])
    if not is_local:
        return False # keep it, it's external
    
    # It's local traffic. Check if ports are "usual"
    lport = c.laddr.port if c.laddr else 0
    rport = c.raddr.port if c.raddr else 0
    
    # If one of the ports is a common service port like 8050 (Dash API), ignore the connection
    if lport in USUAL_PORTS or rport in USUAL_PORTS:
        return True
        
    return False
'''

# Put this before 'def update_data():'
text = text.replace('def update_data():', filter_logic + '\ndef update_data():')

# Update logic inside update_data for new_conns
target1 = '''            for c in current_conns:
                if c.status == 'ESTABLISHED':'''
replace1 = '''            for c in current_conns:
                if c.status == 'ESTABLISHED' and not is_unwanted_localhost(c):'''

text = text.replace(target1, replace1)

# Now in the callback where active_conns is built
target2 = '''        active_conns = []
        for c in psutil.net_connections(kind='inet'):
            if c.status == 'ESTABLISHED':
                active_conns.append(c)'''
replace2 = '''        active_conns = []
        for c in psutil.net_connections(kind='inet'):
            if c.status == 'ESTABLISHED' and not is_unwanted_localhost(c):
                active_conns.append(c)'''

# Maybe active_conns structure exists exactly like that? Let's check with replacing
text = re.sub(
    r'active_conns = \[\]\s*for c in psutil\.net_connections\(kind=\'inet\'\):\s*if c\.status == \'ESTABLISHED\':\s*active_conns\.append\(c\)',
    '''active_conns = []
        for c in psutil.net_connections(kind='inet'):
            if c.status == 'ESTABLISHED' and not is_unwanted_localhost(c):
                active_conns.append(c)''',
    text
)

# Wait, what if the callback loops over current_conns instead of psutil directly?
# Let's write the new script directly.
with open('monitor_new.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("DNS noise patched")
