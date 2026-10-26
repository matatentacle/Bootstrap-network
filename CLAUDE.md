# Bootstrap gateway workspace

Working set for the Bootstrap building network: Zyxel ATP500 (retiring) and FortiGate-120G
(replacing it), the Zyxel switch fabric, and the MINI-PC-6 jump box that is the only host
with a leg on both gateway management networks. Mat Kennedy is the operator.

## Golden rule: read-only until it is not

Both gateways are production (about 44 tenants on the ATP500, eight on the FortiGate).
Show/get/diagnose-style commands are fine without asking (Mat's standing OK, 14 Oct 2026).
Anything that changes state on a gateway or switch needs Mat's go-ahead for that specific
change. No reboots, no re-addressing, no policy or interface edits, never touch Tailscale or
the USB NIC on the box without Mat watching. `bin/jb` enforces this with an allowlist; do not
set `JB_WRITE=1` to get around it. Full rules: `notes/gateway-working-rules.md`.

## What lives where

| Path | What | Committed? |
|---|---|---|
| `bin/` | `jb` (jump box wrapper), `sanitize.py`, `check-secrets.sh` | yes |
| `jumpbox-setup/` | Mirror of `~/jumpbox-setup` on the box: the expect scripts, setup, reports | yes, minus `.env` |
| `configs/` | Sanitised device captures + NOTES.md per device + Bootstrap's workbook and the crossref | yes |
| `FACTS.md` | Fact sheet + index for quick answers; Claude Desktop reads this first. Claude Code keeps it current | yes |
| `notes/` | Working notes and memory files from the jump box sessions (start with `notes/MEMORY.md`) | yes |
| `private/` | Raw captures with their git history (`configs-raw/`), ad-hoc outputs (`captures/`), `jb.env` | **never** |
| `jumpbox-setup/.env` | Gateway credentials. Belongs on the box only; a local copy is ignored | **never** |

Secrets never go in the repo. The FortiGate config's `ENC` blobs are decryptable (private-data-
encryption is off), the ATP500 config carries a reversible PSK, the switches carry admin-password
lines. `bin/sanitize.py import` replaces each with `<REDACTED:fingerprint>`; the pre-commit hook
(`.githooks/pre-commit`) refuses anything that still looks like a secret.

## Claude Desktop reads, Claude Code writes

Claude Desktop is linked to this folder for exploratory questions, emails and documents; it
follows `CLAUDE-DESKTOP.md`. It reads `FACTS.md` (fact sheet plus index) and only opens the files
the index names. Claude Code owns the work and keeps `FACTS.md` current: after any new capture,
crossref run or finding that changes a fact, update the sheet and its "Updated" line. Desktop may
correct a stale line with Mat's OK and marks it "(updated <date> by Claude Desktop)"; check
`git status` at the start of a session and fold such edits in.

## How to do things

- Box health: `bin/jb status`. Shell: `bin/jb shell`.
- Gateway reads: `bin/jb fgt "get system status"`, `bin/jb atp "show interface all"`,
  `bin/jb sw 192.168.1.39 "show vlan"`. Output is streamed back and saved under
  `private/captures/` and `~/captures/` on the box.
- ATP500 full admin (`--admin`) needs a fresh Google Authenticator code from Mat: `ATP_OTP=123456 bin/jb atp --admin "show running-config"`.
- New captures from the box: `bin/jb pull` (git-pulls `/srv/configs`, fetches `~/captures`, sanitises into `configs/`).
- Re-run the workbook cross-reference after a fresh capture: `python -I configs/bootstrap-records/tools/crossref.py configs/bootstrap-records/workbook-2026-10-07 configs configs/bootstrap-records/crossref-<date>`.
- Claude Code in auto mode will not SSH to the gateways directly; always go through the box via `bin/jb`.

## Facts that are easy to get wrong

- Tenants on the FortiGate are VLANs 150 to 175 on the port3+port4 bond, not on 10G x1.
- Bootstrap's workbook (`configs/bootstrap-records/`) is *their* record, not target state. Trust the device captures for what is configured.
- Nebula names (SW01 etc.) are not the switches' system names; the map is in `configs/switches/NOTES.md`.
- Large outputs go to files, not into chat. Mat reads on an old phone: plain text, no artifacts.
