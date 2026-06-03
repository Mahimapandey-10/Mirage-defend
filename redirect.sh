#!/bin/bash
ATTACKER_IP="$1"
LOG_FILE="/home/ubuntu/ghost_protocol.log"
if [ -z "$ATTACKER_IP" ]; then
    echo "[$(date)] ERROR: No IP provided" >> "$LOG_FILE"
    exit 1
fi
echo "[$(date)] BLACKLISTING $ATTACKER_IP" >> "$LOG_FILE"
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A PREROUTING -p tcp -s $ATTACKER_IP --dport 22 -j DNAT \
    --to-destination 172.17.0.2:22
iptables -t nat -A POSTROUTING -d 172.17.0.2 -j MASQUERADE
echo "[$(date)] $ATTACKER_IP → 172.17.0.2:22 (honeypot)" >> "$LOG_FILE"
