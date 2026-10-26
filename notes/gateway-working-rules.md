---
name: gateway-working-rules
description: Mat's standing rules for the Bootstrap gateways (read-only, no reboots, keep the jump box reachable); read-only accounts for both and the ATP500 full admin (2FA) in ~/jumpbox-setup/.env
metadata:
  type: feedback
---

Both gateways are production: read-only commands only, no reboots, no re-addressing, no interface or policy changes unless Mat authorises a specific change. Never touch Tailscale, the ufw tailscale0 rule or the USB NIC link to the ATP500 without Mat watching. Save large outputs under /srv/configs, not in chat. Lockdown findings are logged, never actioned.

Since 14 Oct 2026 both gateways have read-only accounts whose credentials sit in ~/jumpbox-setup/.env (sections `Fortinet` and `APT500`). The ATP500 account no longer needs a Google Authenticator code, ~/jumpbox-setup/atp500-cmd.sh "<cmd>" <outfile> logs in by itself (expect, rewritten 14 Oct 2026) and lands on the `Router>` limited-admin prompt. Limited-admin cannot `show running-config`. For that, `atp500-cmd.sh --admin` uses the full admin MKennedyAdmin (second `APT500` section in .env under `Full Admin accounts`, added back 14 Oct 2026); the gateway still asks for a Google Authenticator code after the password, so ask Mat for a code and pass it as ATP_OTP=123456 (codes expire in 30 s, run straight away). Use --admin only for reads Mat asks for or changes Mat has authorised. Zyxel prompt quirk: arrives as `\r\n\rRouter> `, and a one-line Tcl `expect { pat {act} }` is parsed as a single glob pattern, so always write expect clauses on separate lines. FortiGate access is scripted (fortigate-cmd.sh, fortigate-discover.sh) with `ro-jumpbox`, a `super_admin_readonly` account trusted only from the jump box, created by Mat 23 Oct 2026 and proven the same day. Mat's own `mat` account is super_admin with 2FA (20 Oct 2026) and is the one that makes changes, with Mat at the keyboard.

**Why:** eight live tenants on the FortiGate and about 44 on the ATP500; an outage is not acceptable. Claude Code's auto mode refuses SSH to the gateways, so Mat runs these sessions outside auto mode.
**How to apply:** before any gateway command, check it is read-only; if a change is needed, state it and wait for Mat. Related: [[bootstrap-jumpbox]].
