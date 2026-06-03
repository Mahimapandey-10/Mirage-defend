
# 🌵 Mirage-Defend

**Active Deception & Threat Intelligence Platform**

*Trap. Mirror. Outsmart.*

</div>

---

## 🧠 What is Mirage-Defend?

A **mirage** is an optical illusion — something that looks completely real, but isn't. You see a lake in the desert, you run towards it, and it disappears. The attacker was deceived by the environment itself.

Mirage-Defend applies that exact principle to cybersecurity.

Instead of just **blocking** attackers, we let them in, **trap** them inside a fake server the moment they touch a sensitive file, and **record everything they do** — while they think they're on the real system.

> *The attacker thinks they're inside your system. They're inside your trap.*

---

## 🎯 The Problem

| Problem | What it means |
|---|---|
| **Zero Attacker Visibility** | Traditional tools log breaches but reveal nothing about who did it, how they moved, or what they wanted |
| **Credential Exploitation** | Exposed API keys and database configs are silently weaponised with no interception or tracking |
| **The Dwell Time Problem** | Attackers move freely inside compromised networks for months before anyone notices |

---

## ✅ Our Solution

```
Attacker touches honeyfile
        ↓
inotify fires → Ghost Protocol detects in milliseconds
        ↓
Auth method checked → password login = attacker confirmed
        ↓
iptables DNAT → attacker's IP silently redirected to Docker container
        ↓
Attacker's session dropped naturally (looks like network hiccup)
        ↓
Attacker reconnects → lands in fake server unknowingly
        ↓
Every command logged → live dashboard updated in real time
```

---

## ⚡ Features

- 🔍 **Millisecond Detection** — Kernel-level inotify via Python Watchdog, fires the instant a honeyfile is accessed
- 🔀 **Silent Redirection** — IP-specific iptables DNAT, surgical and completely invisible to the attacker
- 🐳 **Docker Honeypot** — Isolated fake production environment with convincing credentials and file structure
- 🧠 **Smart Auth Detection** — Distinguishes admin (SSH key + trusted IP) vs attacker (password) automatically
- 🗺️ **Live Threat Dashboard** — Flask + D3.js with world map, session tracking, and per-attacker command history
- 🔒 **Zero Admin Lockout** — Only the attacker's specific IP gets redirected, admin access is never affected

---

## 🏗️ Architecture

### Components

```
mirage-defend/
├── ghost_protocol.py          # Core detection engine (Python + Watchdog)
├── redirect.sh                # iptables DNAT redirect script
├── dashboard/
│   ├── app.py                 # Flask backend + geolocation API
│   └── templates/
│       └── dashboard.html     # Live threat intelligence UI (D3.js)
├── honeypot/
│   ├── Dockerfile             # Honeypot container definition
│   └── fake_files/            # Decoy credentials and configs
│       ├── database.yml
│       ├── app_secrets.env
│       └── backup.sql
└── sensitive/                 # Honeyfiles that trigger detection
    ├── SECRET_KEYS.txt
    ├── db_passwords.txt
    └── employee_data.csv
```

### Ghost Protocol (ghost_protocol.py)

The brain of the system. Subscribes to kernel `inotify` events on the sensitive directory via Python Watchdog. When a file is accessed:

1. Checks all active SSH sessions using `who`
2. Looks up each session's auth method via `journalctl`
3. Password auth from untrusted IP = attacker confirmed
4. Fires `redirect.sh` with the attacker's IP
5. Kills the attacker's session naturally (1s delay, feels like network drop)
6. Writes attacker's real IP to honeypot log (bypasses Docker NAT)

### Redirect Script (redirect.sh)

Adds a **single IP-specific** iptables DNAT rule:

```bash
iptables -t nat -A PREROUTING \
    -p tcp -s $ATTACKER_IP --dport 22 \
    -j DNAT --to-destination 172.17.0.2:22
```

Only traffic from the attacker's IP gets redirected. Everyone else — including the admin — connects normally.

### Honeypot Container

Ubuntu 22.04 Docker container with:
- Fake Rails app configs (`database.yml`, `app_secrets.env`, `backup.sql`)
- Seeded bash history to look like a real active server
- Custom `logger.sh` injected as default shell to capture every command
- SSH host keys copied from real server — no fingerprint mismatch warning

### Threat Intelligence Dashboard

- **Flask** backend reads `attacker.log` every 5 seconds
- **D3.js** renders world map with animated attacker location pins
- **ip-api.com** provides geolocation (server-side, no CORS issues)
- Click any attacker IP to see their full command history in a modal

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Cloud Infrastructure | AWS EC2 (Ubuntu 24.04) |
| Detection Engine | Python 3 + Watchdog (inotify) |
| Network Redirect | iptables DNAT + MASQUERADE |
| Honeypot Isolation | Docker |
| Dashboard Backend | Flask |
| Dashboard Frontend | D3.js + Vanilla JS |
| Map Rendering | D3 Natural Earth Projection + world-atlas |
| Geolocation | ip-api.com |
| Auth Detection | journalctl + SSH auth logs |

---

## 🚀 Setup

> **Note:** Deploy on infrastructure you own and control. Honeypots are a well-established, legally accepted defensive security technique used by SOC teams and threat researchers worldwide.

### Prerequisites

- AWS EC2 instance (Ubuntu 24.04 LTS)
- Security group with ports `22`, `2222`, `5000` open
- Docker installed

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/joshads-x/Mirage-defend.git
cd Mirage-defend

# 2. Install dependencies
sudo apt update && sudo apt install -y python3.12-venv docker.io
python3 -m venv mirage-env && mirage-env/bin/pip install watchdog
python3 -m venv dashboard-env && dashboard-env/bin/pip install flask

# 3. Build and run honeypot container
cd honeypot
docker build -t mirage-honeypot .
docker run -d --name honeypot --restart always \
  -p 2222:22 \
  -v /home/ubuntu/honeypot/logs:/var/log \
  mirage-honeypot

# 4. Configure sudoers
echo "ubuntu ALL=(ALL) NOPASSWD: /home/ubuntu/redirect.sh, /sbin/iptables, /usr/sbin/iptables, /usr/bin/pkill" | sudo tee -a /etc/sudoers

# 5. Set up systemd services
sudo systemctl daemon-reload
sudo systemctl enable --now ghost-protocol mirage-dashboard

# 6. Access dashboard
# http://<your-ec2-ip>:5000
```

### After Setup — Two Manual Steps

```bash
# Clear logs for a fresh start
sudo truncate -s 0 /home/ubuntu/ghost_protocol.log
sudo truncate -s 0 /home/ubuntu/honeypot/logs/attacker.log
sudo iptables -t nat -F PREROUTING
sudo iptables -t nat -F POSTROUTING
sudo systemctl restart ghost-protocol
```

---

## 📊 Dashboard

| Panel | What it shows |
|---|---|
| **World Map** | Real-time attacker geolocation with animated ripple pins |
| **Attacker Sessions** | All trapped IPs with timestamps — click to view commands |
| **Alert Feed** | Honeyfile access events with redirect confirmation |
| **Captured Commands** | Every command typed inside the honeypot, newest first |

---

## 🔄 Full Attack Flow

```
┌─────────────────────────────────────────────────────────┐
│                    ATTACKER'S VIEW                      │
│                                                         │
│  ssh ubuntu@server → lands on real server               │
│  cat SECRET_KEYS.txt → "jackpot!"                       │
│  connection drops → "must be wifi"                      │
│  ssh ubuntu@server → same IP, same port                 │
│  ls, whoami, cat database.yml → "I'm in!"               │
│                                                         │
│               (they're in our trap)                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    DEFENDER'S VIEW                      │
│                                                         │
│  Ghost Protocol: ALERT — SECRET_KEYS.txt accessed       │
│  Ghost Protocol: ATTACKER confirmed — password auth     │
│  Ghost Protocol: BLACKLIST — redirecting IP             │
│  Ghost Protocol: SESSION KILLED — natural disconnect    │
│  Dashboard: New attacker pin — New Delhi, IN            │
│  Dashboard: Commands captured — ls, whoami, cat...      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🏆 Built By

**Cyber Warriors** — Built for a college hackathon.

*Every intrusion is a lesson. We built the classroom.*

---
