#!/usr/bin/env bash
# Jumpbox setup for MINI-PC-6 (Ubuntu 22.04, amd64)
# Terminal-only jumpbox: SSH + Tailscale SSH, no desktop.
# Run as:  sudo bash ~/jumpbox-setup/setup.sh
# Idempotent: safe to re-run. Logs to /var/log/jumpbox-setup.log
set -euo pipefail

if [[ $EUID -ne 0 ]]; then echo "Run with sudo: sudo bash $0"; exit 1; fi

LOG=/var/log/jumpbox-setup.log
touch "$LOG"; chmod 600 "$LOG"
exec > >(tee -a "$LOG") 2>&1
echo "=== jumpbox setup started $(date -Is) ==="

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1
APT="apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Management VLAN subnets of the two gateways to advertise over Tailscale, e.g. "10.10.1.0/24,10.20.1.0/24".
# Leave empty on the bench.
ADVERTISE_ROUTES=""
TARGET_USER="tentacle"

step() { echo; echo "##### $* #####"; }

# ---------------------------------------------------------------- 1. free space
step "1/8 Free disk space before upgrading"
df -h / | tail -1
apt-get clean
journalctl --vacuum-size=100M --vacuum-time=14d || true
# keep only 2 snap revisions and drop disabled ones
snap set system refresh.retain=2 || true
snap list --all 2>/dev/null | awk '/disabled/{print $1, $3}' | while read -r name rev; do
  snap remove "$name" --revision="$rev" || true
done
rm -rf /var/lib/snapd/cache/* 2>/dev/null || true
# RealVNC (long gone) was the only i386 package on the box
if dpkg -l realvnc-vnc-server 2>/dev/null | grep -q '^ii'; then
  $APT purge realvnc-vnc-server || true
fi
if dpkg --print-foreign-architectures | grep -q i386; then
  if ! dpkg -l | awk '$1=="ii" && $2 ~ /:i386$/' | grep -q .; then
    dpkg --remove-architecture i386 || true
  fi
fi
df -h / | tail -1
AVAIL_MB=$(df --output=avail -m / | tail -1)
if (( AVAIL_MB < 2000 )); then
  echo "WARNING: only ${AVAIL_MB}MB free. The upgrade needs ~2GB headroom. Continuing, but it may fail."
fi

# ---------------------------------------------------------------- 2. update
step "2/8 apt update + full-upgrade (644 packages pending at time of writing)"
apt-get update
$APT -o APT::Keep-Downloaded-Packages=false install --only-upgrade apt dpkg libc6 || true
$APT -o APT::Keep-Downloaded-Packages=false full-upgrade
apt-get clean

# ---------------------------------------------------------------- 3. tools
step "3/8 Install jumpbox tooling"
$APT install \
  curl wget git vim nano tmux screen htop btop ncdu tree jq \
  bash-completion fzf ripgrep bat fd-find \
  openssh-client mosh rsync sshfs \
  net-tools dnsutils iputils-ping iputils-tracepath traceroute mtr-tiny whois ipcalc \
  nmap tcpdump iftop nload iperf3 socat netcat-openbsd telnet arp-scan ethtool \
  wireguard-tools \
  minicom picocom usbutils pciutils \
  lsof strace smartmontools lm-sensors \
  zip unzip p7zip-full \
  nfs-common cifs-utils \
  python3 python3-pip python3-venv \
  ca-certificates gnupg lsb-release apt-transport-https software-properties-common \
  ufw fail2ban unattended-upgrades needrestart
# iperf3 may ask about a daemon; make sure it's not running as a service
systemctl disable --now iperf3 2>/dev/null || true

# ---------------------------------------------------------------- 4. tailscale
step "4/8 Tailscale"
if ! command -v tailscale >/dev/null; then
  install -d -m 0755 /usr/share/keyrings
  curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.noarmor.gpg -o /usr/share/keyrings/tailscale-archive-keyring.gpg
  curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.tailscale-keyring.list -o /etc/apt/sources.list.d/tailscale.list
  apt-get update
  $APT install tailscale
fi
systemctl enable --now tailscaled
# Try to bring it up; this prints a login URL and gives up after 30s if nobody authorises it.
# Finish later with:  sudo tailscale up --ssh
if ! tailscale status >/dev/null 2>&1; then
  tailscale up --ssh --timeout 30s || echo "Tailscale not authorised yet. Run: sudo tailscale up --ssh"
fi

# ---------------------------------------------------------------- 5. headless + tailscale ssh
step "5/8 Headless (no desktop) + Tailscale SSH"
apt-mark manual network-manager netplan.io linux-firmware openssh-server tailscale ufw fail2ban zram-tools linux-generic-hwe-22.04 grub-pc >/dev/null
systemctl set-default multi-user.target
for p in ubuntu-desktop ubuntu-desktop-minimal gnome-shell gdm3 gnome-session ubuntu-session xserver-xorg-core xorg xwayland rustdesk mumble; do
  dpkg -l "$p" 2>/dev/null | grep -q '^ii' && $APT purge "$p"
done
rm -f /etc/systemd/system/rustdesk.service /root/rustdesk-password.txt
# zram swap for a 1.8 GB box
$APT install zram-tools
printf 'ALGO=zstd\nPERCENT=50\nPRIORITY=100\n' > /etc/default/zramswap
systemctl enable --now zramswap
tailscale up --ssh --timeout 30s || echo "Tailscale not authorised yet. Run: sudo tailscale up --ssh"
# Subnet routing for the gateway side is opt-in: set ADVERTISE_ROUTES above, or use subnet-router.sh later.
if [[ -n "$ADVERTISE_ROUTES" ]]; then
  bash "$HERE/subnet-router.sh" on "$ADVERTISE_ROUTES"
fi

# ---------------------------------------------------------------- 6. ssh + firewall
step "6/8 SSH hardening, fail2ban, ufw, unattended-upgrades"
systemctl enable --now ssh
cat > /etc/ssh/sshd_config.d/50-jumpbox.conf <<'SSHD'
# Jumpbox hardening (password auth left ON: no authorized_keys exist yet.
# Once a key is in ~/.ssh/authorized_keys, add: PasswordAuthentication no)
PermitRootLogin no
MaxAuthTries 4
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowTcpForwarding yes
AllowAgentForwarding yes
SSHD
if sshd -t; then systemctl reload ssh; else echo "sshd config test FAILED; removing override"; rm -f /etc/ssh/sshd_config.d/50-jumpbox.conf; fi

cat > /etc/fail2ban/jail.d/jumpbox.local <<'F2B'
[sshd]
enabled = true
maxretry = 5
findtime = 10m
bantime = 1h
ignoreip = 127.0.0.1/8 ::1 100.64.0.0/10
F2B
systemctl enable --now fail2ban
systemctl restart fail2ban

ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw limit 22/tcp comment 'SSH (rate limited)'
ufw allow 60000:61000/udp comment 'mosh'
ufw allow in on tailscale0 comment 'tailscale'
ufw --force enable

cat > /etc/apt/apt.conf.d/20auto-upgrades <<'AU'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
AU
systemctl enable --now unattended-upgrades

# ---------------------------------------------------------------- 7. cleanup
step "7/8 Post-upgrade cleanup"
$APT autoremove --purge
apt-get clean
journalctl --vacuum-size=100M || true
snap list --all 2>/dev/null | awk '/disabled/{print $1, $3}' | while read -r name rev; do
  snap remove "$name" --revision="$rev" || true
done
fstrim -av 2>/dev/null || true
cat > /etc/update-motd.d/99-jumpbox <<'MOTD'
#!/bin/sh
echo
echo " Jumpbox: $(hostname)   LAN: $(hostname -I | awk '{print $1}')   Tailscale: $(tailscale ip -4 2>/dev/null || echo 'not up')"
echo " Disk free: $(df -h / | awk 'NR==2{print $4}')   Mem free: $(free -m | awk 'NR==2{print $7}')MB"
echo
MOTD
chmod +x /etc/update-motd.d/99-jumpbox

# ---------------------------------------------------------------- 8. summary
step "8/8 Summary"
df -h / | tail -1
echo "Kernel running: $(uname -r)   Kernel installed: $(ls /boot/vmlinuz-* | sort -V | tail -1 | sed 's#.*/vmlinuz-##')"
echo "Tailscale: $(tailscale status --peers=false 2>/dev/null | head -1 || echo 'not authorised, run: sudo tailscale up --ssh')"
ufw status | head -3
[[ -f /var/run/reboot-required ]] && echo ">>> REBOOT REQUIRED: sudo reboot" || echo "No reboot required."
echo "=== jumpbox setup finished $(date -Is) ==="
