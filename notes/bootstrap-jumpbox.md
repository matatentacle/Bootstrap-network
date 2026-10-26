---
name: bootstrap-jumpbox
description: MINI-PC-6 terminal-only jump box into the Bootstrap gateways (ATP500 + FortiGate-120G); current state as of 13 Oct 2026 and what is still open
metadata:
  node_type: memory
  type: project
  originSessionId: 089dd03d-e83a-4e8f-9f9f-2a8a44d3f4ce
  modified: 2026-10-14T10:53:25.843Z
---

MINI-PC-6 (Celeron J1800, 1.8 GB RAM, Ubuntu 22.04, kernel 6.8) is a terminal-only jump box, racked 13 Oct 2026. Tailscale 100.83.139.20 with Tailscale SSH. USB NIC enx503eaacea0c4 → ATP500 ge7 (DHCP .100, no reservation; only leg with internet, carries the default route). Onboard enp3s0 → FortiGate mgmt 192.168.10.99, static 192.168.10.98 via NetworkManager profile `fortigate-mgmt`, never-default. Subnet routing turned on 14 Oct 2026 at Mat's request (helper ~/jumpbox-setup/subnet-router.sh): advertises 192.168.254.0/24 (ATP500 GUI https://192.168.254.1:50483) and 192.168.10.0/24 (FortiGate GUI https://192.168.10.99); ip_forward=1, ufw FWD rules tailscale0 -> both NICs. Mat must approve the routes in the Tailscale admin console; the box has no Tailscale API key. Sudo password in ~/.claude/.env as `label - password`; gateway creds in ~/jumpbox-setup/.env (renamed from .creds 14 Oct 2026; sections `Fortinet` and `APT500`, read-only FortiGate `mat` and ATP500 `read-only`, plus ATP500 full admin MKennedyAdmin under `Full Admin accounts`, still 2FA).

Discovery on both gateways is done and committed in the git repo /srv/configs (NOTES.md per gateway). FortiGate-120G FW-120G-01, FortiOS 7.4.12, serial FG120GTK24015905; only the read-only admin `mat` is visible; tenants are VLANs 150–175 on the port3+port4 bond (handover's "150–157 on 10G" was wrong); HTTPS admin is exposed on WAN x4. ATP500 5.43(ABFU.0); admins include an unknown full-admin "Shopna".

**Why:** Mat wants the box as the way into both gateways during the ATP500 → FortiGate migration; lockdown comes later.
**How to apply:** Read ~/jumpbox-setup/README.md first (the single live doc; archive/ holds superseded ones). Open items: FortiGate console lead on the box since 26 Oct 2026 (PL2303 /dev/ttyUSB0, proven; reboot-with-lead test still to do); ATP500 console lead not cabled; ser2net waiting on both; .10 reservation vs pin .100; Zyxel port 10 cable; identify Shopna; ATP500 startup config to commit; SSH key then password auth off. See [[gateway-working-rules]] before touching either gateway and [[mat-operator]] for how to deliver output.
