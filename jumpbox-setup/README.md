# Jump box MINI-PC-6 — current state

Updated 2026-10-14. This is the one live document for the box. Superseded material is in archive/ with notes on what changed. Gateway facts live in /srv/configs/*/NOTES.md; tonight's report is DISCOVERY-REPORT-2026-10-13.txt.

## Working rules (from Mat, still in force)
- Read-only on both gateways. No reboots, no re-addressing, no interface or policy changes on the FortiGate or the ATP500 unless Mat says so for a specific change. Eight live tenants on the FortiGate, about 44 on the ATP500.
- Keep the box reachable: never touch Tailscale, the ufw tailscale0 rule, or the USB NIC link to the ATP500 without Mat watching.
- No FortiGate `maintainer` recovery (needs a reboot).
- 1.8 GB RAM, Celeron J1800: no heavy tooling, no containers.
- Large command output goes to /srv/configs, not into chat.

## The box
Ubuntu 22.04, kernel 6.8 HWE, terminal only (desktop, RustDesk, snaps and snapd removed 13 Oct). Disk 64% used.

| Interface | Goes to | Address | Notes |
|---|---|---|---|
| enx503eaacea0c4 (TP-Link UE300 USB, r8152) | ATP500 ge7 | 192.168.254.100/24 by DHCP | The only leg with internet. Carries the default route and Tailscale. No reservation on the ATP500. |
| enp3s0 (onboard) | FortiGate mgmt | 192.168.10.98/24 static | NetworkManager profile `fortigate-mgmt`, never-default. Direct cable, dead end. |
| tailscale0 | tailnet | 100.83.139.20 | Tailscale SSH on. Subnet routing on since 14 Oct 2026: advertises 192.168.254.0/24 (ATP500) and 192.168.10.0/24 (FortiGate); routes must be approved in the Tailscale admin console. |

Services: openssh-server with hardening drop-in (password auth still on, no key yet), fail2ban on sshd, ufw (deny in; rate-limited 22; mosh; all on tailscale0), unattended security upgrades, zram swap. ser2net installed but disabled.

Tooling: tmux, htop, btop, ncdu, git, vim, curl, jq, fzf, ripgrep, mosh, nmap, tcpdump, iftop, iperf3, socat, mtr, wireguard-tools, minicom, picocom, expect, sshpass, smartmontools, python3, NFS/CIFS clients.

Sudo password: ~/.claude/.env, format `label - password`. Gateway credentials: ~/jumpbox-setup/.env (owner-only, lines `Username - x` / `Pass - x`). Top part: read-only accounts, sections `Fortinet` (mat) and `APT500` (read-only). Below the `Full Admin accounts` header: a second `APT500` section with the full admin MKennedyAdmin, added back 14 Oct 2026 for when a config dump or a change is needed; it still needs a Google Authenticator code. No FortiGate admin yet. Renamed from .creds on 14 Oct 2026.

## Reaching things
- Box: `ssh tentacle@100.83.139.20` (Tailscale SSH or plain SSH; Mat normally uses plain SSH).
- FortiGate: `ssh ro-jumpbox@192.168.10.99` from the box, password in the `Fortinet` section of .env. HTTPS 443 on the same address. **23 Oct 2026:** `ro-jumpbox` is a `super_admin_readonly` account with trusted hosts limited to the jump box (192.168.10.98 now, 192.168.5.98 after the management move) and no 2FA; the scripts use it. Mat's own `mat` account is super_admin with 2FA since 20 Oct 2026 and sits at the bottom of .env for reference; scripted logins with it stop at the token prompt (exit 6; `FGT_OTP=<code>` for a one-off). The scripts take the first `Username` under `Fortinet`, so keep `ro-jumpbox` first. `Pass - ` and `Password - ` are both accepted since 23 Oct.
- ATP500: `ssh read-only@192.168.254.1` from the box with the password in .env (account `read-only`), no 2FA code needed any more (changed by Mat 14 Oct 2026). Lands on the `Router>` limited-admin prompt. Use atp500-cmd.sh for scripted commands. Gotchas for anyone scripting it by hand: set TERM=vt100, and the prompt arrives as `\r\n\rRouter> ` (bare CR before the prompt), so anchor on `\r?\n\r?Router> `. Full admin: `atp500-cmd.sh --admin` uses MKennedyAdmin (prompt `Router#`); the gateway asks for a Verification code after the password, so Mat supplies a fresh code as `ATP_OTP=123456`. HTTPS on port 50483.
- Gateway web UIs from a laptop: `ssh -L 8443:<gateway-ip>:443 tentacle@100.83.139.20`, or `ssh -D 1080 ...` for a SOCKS proxy.

## Scripts in this folder
| Script | Purpose |
|---|---|
| setup.sh | Idempotent rebuild of the box as a terminal-only jump box. Logs to /var/log/jumpbox-setup.log. |
| fortigate-discover.sh | Read-only FortiGate command set over SSH, outputs to /srv/configs/fortigate/. |
| atp500-cmd.sh | `[--admin] "<command>" <outfile>`: logs in to the ATP500, runs one ZLD command, pages through --More--, saves clean output. Same shape as fortigate-cmd.sh. Default account is `read-only` (no 2FA, cannot `show running-config`). `--admin` uses MKennedyAdmin and needs `ATP_OTP=<code>` in the environment; without it the script stops at the code prompt with exit 6. Rewritten 14 Oct 2026; the tmux-session version is in archive/. |
| zyxel-sw-cmd.sh | `<ip> "<command>" <outfile>`: one read-only ZyNOS command on a Zyxel switch, Zyxel section of .env. |
| fortigate-cmd.sh | `"<command>" <outfile>`: one read-only FortiOS command, `ro-jumpbox` account (first `Fortinet` entry in .env). |
| subnet-router.sh | `on <cidr>[,<cidr>]` / `off`: Tailscale subnet routing for the gateway management networks. On since 14 Oct 2026 for 192.168.254.0/24,192.168.10.0/24. |

## Config repo
/srv/configs is a git repo. atp500/ and fortigate/ each hold NOTES.md plus dated raw outputs and the full configs captured 13 Oct. Credentials never go in it.

## Open items
1. FortiGate console lead: done 26 Oct 2026. Prolific PL2303 adapter (067b:23a3) on the NEC hub, /dev/ttyUSB0, 9600 8N1; tentacle added to dialout the same day. Proven from the box: one Enter returns `FW-120G-01 login:`. Use `picocom -b 9600 /dev/ttyUSB0` (quit Ctrl-A Ctrl-X). Warning: a lead on this port held the FortiGate at its BIOS boot menu for 46 h on 24 to 26 Oct (any console input at boot does that). Either test a reboot with this lead in during a quiet window, or enable BIOS restricted mode (Ctrl-B only) first; Mat prefers the reboot test (26 Oct). Full admin on the FortiGate is now possible from here.
2. ATP500 console lead not cabled (115200 8N1). Then ser2net (udev by FTDI serial, ports 2001/2002 bound to the Tailscale IP).
3. Jump box address on the ATP500 side: DHCP reservation for .10 in a change window, or pin .100 statically on the box.
4. Confirm which cable is on Zyxel switch 101 port 10; tenants are on the FortiGate's port3+port4 bond, not x1. Needs switch credentials (none held); see Switch layer below.
5. Identify the ATP500 full-admin account "Shopna".
6. Copy the ATP500 startup config from Mat's machine into /srv/configs/atp500 and commit.
7. Add an SSH key to ~/.ssh/authorized_keys, then set `PasswordAuthentication no` in /etc/ssh/sshd_config.d/50-jumpbox.conf and reload ssh.
8. Four core i386 packages remain (libc6, libcrypt1, libgcc-s1, gcc-12-base); harmless. Removal needs `--allow-remove-essential`.
9. Lockdown-phase findings are listed in DISCOVERY-REPORT-2026-10-13.txt and both NOTES.md files. None actioned.

## Switch layer (added 14 Oct 2026)
Full map in /srv/configs/switches/NOTES.md, raw per-switch outputs in /srv/configs/switches/raw/, plain-text summary in SWITCH-MAP-2026-10-14.txt.
Core is SW01 (192.168.1.39, GS1920-24HP): ATP500 LAN1 on port 2, FortiGate LAN-Bond-2 on ports 9+10 (LACP, trunk group T1), downstream switches on 23 and 25-28. 192.168.1.38 is a second hub. 18 switches in all (13x GS1920-24HP, 1x GS1920-8HP, 2x GS1350-6HP, 2x Cisco SB). All Zyxel kit is Nebula-managed; SSH with the ".env" Zyxel admin works on the GS1920s (read-only use only), the two GS1350s refuse it, the Cisco pair have no SSH. FortiGate x1 (192.168.201.x) is a separate fabric not reachable from the box.
`zyxel-sw-cmd.sh <ip> "<cmd>" <outfile>` runs one ZyNOS command (handles prompts with spaces and the ESC-7 sequences the GS1920 emits). Useful commands: show system-information, show lldp info remote, show vlan, show trunk, show interfaces status, show mac address-table all, show running-config. `fortigate-cmd.sh "<cmd>" <outfile>` does the same for one FortiOS command.
## Bootstrap's own records (added 14 Oct 2026)
Their "VLANs and Configurations" workbook (7 Oct 2026, plus the Dec 2025 copy) is ingested into
/srv/configs/bootstrap-records/ with a CSV per tab and a cross-reference against the device captures
(crossref-2026-10-14/). It is their record, not our target state: use it for tenant names, rooms and
what they intend (intent-notes.txt), and trust the device captures for what is actually configured.
Plain-text summary: BOOTSTRAP-SHEET-CROSSREF-2026-10-14.txt. Re-run tools/crossref.py after a fresh capture.
