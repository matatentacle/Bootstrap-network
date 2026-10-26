# Bootstrap network workspace

Everything needed to monitor, diagnose and talk to the Bootstrap gateways (Zyxel ATP500, retiring;
FortiGate-120G, replacing it) and the switch fabric behind them, from any machine, through the
MINI-PC-6 jump box. Packaged from the box on 20 Oct 2026.

**Golden rule: read-only until it is not.** Both gateways carry live tenants. Read commands are
fine; anything that changes state needs Mat's go-ahead for that specific change. See
`notes/gateway-working-rules.md`.

## Key addresses

| What | Address | Notes |
|---|---|---|
| Jump box (MINI-PC-6) | `mini-pc-6` / 100.83.139.20 on Tailscale, user `tentacle` | SSH key auth; `bin/jb status` |
| Jump box leg to ATP500 | 192.168.254.100 (USB NIC, DHCP) | only leg with internet, carries Tailscale |
| Jump box leg to FortiGate | 192.168.10.98 (onboard NIC, static) | dead end |
| ATP500 management | 192.168.254.1 on ge7 | HTTPS 50483, SSH 22, 2FA on full admins |
| FortiGate-120G management | 192.168.10.99 on mgmt | HTTPS 443, SSH 22; moving to 192.168.5.0/24 (decided 23 Oct 2026, not yet done) |
| Core switch SW01 | 192.168.1.39 | GS1920-24HP; second hub SW02 is 192.168.1.38 |
| Tenant gateways | 192.168.N.254 | ATP500 VLANs 10 to 74, FortiGate VLANs 150 to 175 |

Full fact sheet and index: `FACTS.md`.

## Get working on a new machine

1. Clone the repo and turn on the secrets guard:

       git clone <repo-url> bootstrap-workspace && cd bootstrap-workspace
       git config core.hooksPath .githooks

2. Make sure you can reach the box. It is on the Tailscale tailnet as `mini-pc-6`
   (100.83.139.20), user `tentacle`, SSH key auth. Add an entry to `~/.ssh/config` if you like
   and point the wrapper at it:

       echo 'JB_HOST=mini-pc-6' > private/jb.env     # optional; default is tentacle@100.83.139.20

3. Check it works:

       bin/jb status                      # Windows: bin\jb.cmd status, or run from Git Bash

   That prints links, routes, Tailscale state and whether each gateway answers ping. Nothing
   on the laptop needs gateway credentials: they live only in `~/jumpbox-setup/.env` on the box.

4. Read `notes/MEMORY.md`, then `jumpbox-setup/README.md` (the box's own live document), then the
   `NOTES.md` in each `configs/` subfolder.

Requirements on the laptop: git, ssh, python 3 (standard library only). `bin/jb` is bash; on
Windows it runs under Git Bash via `bin/jb.cmd`.

## Day to day

    bin/jb fgt "get system status"               one FortiOS command, read-only account
    bin/jb atp "show interface all"              one ATP500 command, limited-admin account
    bin/jb sw 192.168.1.39 "show lldp info remote"   one command on a Zyxel GS1920
    bin/jb shell                                 interactive shell on the box
    bin/jb pull                                  bring new captures down and sanitise them into configs/

Each gateway command is checked against a read-only allowlist (show, get, display, ping,
traceroute, safe diagnose subtrees). Output streams back and is saved under `private/captures/`
here and `~/captures/` on the box. ATP500 full admin: `ATP_OTP=<code> bin/jb atp --admin "<cmd>"`
with a fresh Google Authenticator code from Mat.

## Layout

    bin/              jb (wrapper), sanitize.py (capture import + secret check), check-secrets.sh
    jumpbox-setup/    mirror of ~/jumpbox-setup on the box: expect scripts, setup.sh, reports, archive/
                      .env is ignored; .env.example shows the shape
    configs/          sanitised captures: atp500/, fortigate/, switches/, bootstrap-records/ (their
                      VLAN workbook + crossref). NOTES.md in each folder holds the findings.
    notes/            working notes from the jump box sessions; notes/MEMORY.md is the index
    private/          NOT committed. configs-raw/ (raw captures with their git history, pulled from
                      /srv/configs on the box), captures/ (ad-hoc outputs), jb.env

## What is kept out of git, and why

- `jumpbox-setup/.env` and anything named `*.env`: plaintext gateway and switch credentials.
- `private/`: raw captures. The FortiGate config was taken with `private-data-encryption disable`,
  so its `ENC` blobs are recoverable with public tooling; the ATP500 config holds a reversible
  ZyMesh PSK and admin hashes; the switch configs hold `admin-password` and RADIUS key lines.
- Committed captures have each of those replaced with `<REDACTED:xxxxxxxx>` (first 8 hex of the
  SHA-256 of the secret), so you can still see whether a value changed between captures.
- `.githooks/pre-commit` runs `bin/sanitize.py check` on every staged file and refuses secrets.
  `bin/check-secrets.sh` scans the whole tree on demand.

The repo still contains tenant names, internal addressing, MAC addresses, public IP allocations
and three personal email addresses in Bootstrap's workbook. Keep the GitHub repo private.

## The box in one paragraph

Ubuntu 22.04 on a Celeron J1800 with 1.8 GB RAM, terminal only. USB NIC to ATP500 ge7
(192.168.254.100 by DHCP, the only leg with internet, carries Tailscale); onboard NIC to the
FortiGate mgmt port (192.168.10.98 static, dead end). Tailscale subnet routing advertises both
management networks. `/srv/configs` on the box is the raw capture repo; `~/jumpbox-setup/` holds
the scripts and credentials. Details and open items: `jumpbox-setup/README.md`.
