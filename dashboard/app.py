
from flask import Flask, render_template, jsonify
from flask_cors import CORS

app=Flask(__name__)
CORS(app)

import re, os, json
try:
    import urllib.request
except:
    pass

LOG_FILE = "/home/ubuntu/honeypot/logs/attacker.log"
GEO_CACHE = {}

def is_real_ip(ip):
    return ip and not ip.startswith('172.17.') and not ip.startswith('172.18.') \
           and not ip.startswith('10.') and not ip.startswith('192.168.') \
           and ip != 'unknown'

def geo_lookup(ip):
    if ip in GEO_CACHE:
        return GEO_CACHE[ip]
    try:
        url = f"http://ip-api.com/json/{ip}?fields=lat,lon,city,country,countryCode"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            if data.get('lat'):
                GEO_CACHE[ip] = data
                return data
    except:
        pass
    return None

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/geo/<ip>")
def geo(ip):
    if not is_real_ip(ip):
        return jsonify({"error": "invalid ip"}), 400
    data = geo_lookup(ip)
    if data:
        return jsonify(data)
    return jsonify({"error": "not found"}), 404

@app.route("/api/data")
def api_data():
    sessions, commands, ips = [], [], []
    commands_by_ip = {}
    current_ip = None
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            for line in f:
                m = re.match(r'\[\+\] Session started: (.+)', line)
                if m:
                    sessions.append({"started": m.group(1), "ip": None})
                m = re.match(r'\[\+\] Remote IP: (.+)', line)
                if m:
                    current_ip = m.group(1).strip()
                    if sessions:
                        sessions[-1]["ip"] = current_ip
                    if current_ip not in ips:
                        ips.append(current_ip)
                    if current_ip not in commands_by_ip:
                        commands_by_ip[current_ip] = []
                m = re.match(r'\[CMD (\d{2}:\d{2}:\d{2})\] (.+)', line)
                if m:
                    cmd = {"time": m.group(1), "command": m.group(2).strip()}
                    commands.append(cmd)
                    if current_ip and current_ip in commands_by_ip:
                        commands_by_ip[current_ip].append(cmd)
    return jsonify({
        "sessions": sessions,
        "commands": list(reversed(commands)),
        "commands_by_ip": commands_by_ip,
        "total_commands": len(commands),
        "total_sessions": len(sessions),
        "unique_ips": ips
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
