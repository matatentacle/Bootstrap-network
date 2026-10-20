#!/usr/bin/env bash
# Tailscale subnet routing for the two gateway management VLANs.
#   sudo bash ~/jumpbox-setup/subnet-router.sh on  <cidr>[,<cidr>...]
#   sudo bash ~/jumpbox-setup/subnet-router.sh off
# Example: sudo bash ~/jumpbox-setup/subnet-router.sh on 10.10.1.0/24,10.20.1.0/24
# Forwarding is allowed from tailscale0 out of every physical NIC (enp3s0 = gateway A, enx... = gateway B).
# After "on", approve the routes in the Tailscale admin console (Machines -> mini-pc-6 -> Edit route settings).
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "run with sudo"; exit 1; }
MODE="${1:-}"; ROUTES="${2:-}"
NICS=$(ip -br link | awk '{print $1}' | grep -vE '^(lo|tailscale0)$')
case "$MODE" in
  on)
    [[ -n "$ROUTES" ]] || { echo "give the management subnet(s), e.g. 10.10.1.0/24,10.20.1.0/24"; exit 1; }
    printf 'net.ipv4.ip_forward = 1\nnet.ipv6.conf.all.forwarding = 1\n' > /etc/sysctl.d/99-tailscale.conf
    sysctl -p /etc/sysctl.d/99-tailscale.conf >/dev/null
    for i in $NICS; do ufw route allow in on tailscale0 out on "$i" comment "tailscale -> $i" >/dev/null; done
    tailscale set --advertise-routes="$ROUTES"
    echo "Advertising $ROUTES (forwarding out of: $(echo $NICS)). Approve in the Tailscale admin console."
    ;;
  off)
    tailscale set --advertise-routes=
    for i in $NICS; do ufw --force route delete allow in on tailscale0 out on "$i" >/dev/null 2>&1 || true; done
    rm -f /etc/sysctl.d/99-tailscale.conf
    sysctl -w net.ipv4.ip_forward=0 net.ipv6.conf.all.forwarding=0 >/dev/null
    echo "Subnet routing off."
    ;;
  *) sed -n '2,7p' "$0"; exit 1;;
esac
tailscale status --peers=false | head -1
