import subprocess, time, os, ipaddress
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = "/home/ubuntu/sensitive"
LOG_FILE = "/home/ubuntu/ghost_protocol.log"
REDIRECT_SCRIPT = "/home/ubuntu/redirect.sh"
ATTACKER_LOG = "/home/ubuntu/honeypot/logs/attacker.log"
TRUSTED_NETWORK = ipaddress.ip_network("13.233.177.0/29")

def log(msg):
    line = f"[{datetime.now()}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def write_attacker_session(ip):
    """Write session info directly to attacker log from host — bypasses Docker NAT issue"""
    try:
        with open(ATTACKER_LOG, "a") as f:
            f.write(f"[+] Session started: {datetime.now().strftime('%a %b %d %H:%M:%S UTC %Y')}\n")
            f.write(f"[+] Remote IP: {ip}\n")
        log(f"ATTACKER LOG: Session entry written for {ip}")
    except Exception as e:
        log(f"ATTACKER LOG WRITE FAILED: {e}")

def get_all_sessions():
    try:
        output = subprocess.check_output(
            "who | awk '{print $5}' | tr -d '()' | grep -v '^$'",
            shell=True, text=True).strip()
        if not output:
            return []
        return list(set(output.splitlines()))
    except:
        return []

def get_auth_method(ip):
    try:
        result = subprocess.check_output(
            f"journalctl -u ssh -n 200 --no-pager | grep 'Accepted' | grep '{ip}' | tail -1",
            shell=True, text=True).strip()
        if "publickey" in result:
            return "publickey"
        elif "password" in result:
            return "password"
        return "unknown"
    except:
        return "unknown"

def is_trusted(ip):
    try:
        in_trusted_range = ipaddress.ip_address(ip) in TRUSTED_NETWORK
    except:
        in_trusted_range = False
    auth_method = get_auth_method(ip)
    if auth_method == "publickey" and in_trusted_range:
        log(f"WHITELIST: {ip} — publickey + trusted range. Admin access.")
        return True
    if auth_method == "publickey" and not in_trusted_range:
        log(f"SUSPICIOUS: {ip} — publickey but NOT in trusted range. Redirecting.")
        return False
    if auth_method == "password":
        log(f"ATTACKER: {ip} — password auth detected. Redirecting.")
        return False
    log(f"WARNING: {ip} — auth method unknown. Redirecting.")
    return False

def kill_attacker_session(ip):
    try:
        who_line = subprocess.check_output(
            f"who | grep '{ip}'",
            shell=True, text=True).strip()
        if not who_line:
            log(f"SESSION KILL: No active pts found for {ip}")
            return
        pts = who_line.split()[1]
        log(f"SESSION KILL: Killing {pts} for {ip}")
        subprocess.run(f"sudo bash -c 'echo \"\" > /dev/{pts}'", shell=True)
        subprocess.run(["sudo", "pkill", "-9", "-t", pts])
        log(f"SESSION KILLED: {ip} disconnected naturally")
    except Exception as e:
        log(f"SESSION KILL FAILED: {e}")

class HoneyfileHandler(FileSystemEventHandler):
    def __init__(self):
        self.blacklisted_ips = set()

    def on_any_event(self, event):
        if event.is_directory:
            return
        active_sessions = get_all_sessions()
        if not active_sessions:
            return
        fname = os.path.basename(event.src_path)
        log(f"ALERT | File: {fname} | Event: {event.event_type} | Sessions: {active_sessions}")
        for ip in active_sessions:
            if ip in self.blacklisted_ips:
                log(f"ALREADY BLACKLISTED: {ip}")
                continue
            if is_trusted(ip):
                continue
            self.blacklisted_ips.add(ip)
            log(f"BLACKLIST: Redirecting {ip} to honeypot.")
            subprocess.Popen(["sudo", REDIRECT_SCRIPT, ip])
            time.sleep(1)
            kill_attacker_session(ip)
            # Write real IP to attacker log from host — fixes Docker NAT problem
            time.sleep(2)
            write_attacker_session(ip)

if __name__ == "__main__":
    log("Ghost Protocol started")
    log(f"Watching: {WATCH_DIR}")
    log(f"Trusted network: {TRUSTED_NETWORK}")
    observer = Observer()
    handler = HoneyfileHandler()
    observer.schedule(handler, WATCH_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
