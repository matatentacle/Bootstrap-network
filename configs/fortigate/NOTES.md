# FortiGate notes — updated 2026-10-13

Management 192.168.10.99 on interface `mgmt`, reached from jump box enp3s0 (192.168.10.98/24, no default route).
Source files: system-status, interface-physical, show-interface, performance, show-admin, ha-status, routing-table, full-config (45,286 lines, complete).

## Identity
| Item | Value |
|---|---|
| Model | FortiGate-120G |
| Firmware | v7.4.12 build 2902 (GA) |
| Serial | FG120GTK24015905 |
| Hostname | FW-120G-01 |
| HA | standalone |
| Last reboot reason | power cycle |
| FortiCare | Enforce, security level High |
| Load at capture | CPU ~4%, idle 96% |

## Ports
| Port | State | Role |
|---|---|---|
| mgmt | up 1G | 192.168.10.99/24, allowaccess ping https ssh |
| x4 | up 10G | WAN "Vorboss" 193.221.132.138/29, default via .137; secondary 193.221.131.33/27 |
| x1 | up 10G | alias "LAN" 192.168.201.1/24; parent of vlan70 and vlan200-TEST |
| port3 + port4 | up 1G each | aggregate **LAN-Bond-2**, parent of all tenant VLANs 150–175 |
| x2 + x3 | down | members of the `fortilink` aggregate (so x2 exists but is not free in config) |
| port1 | down | parent of vlan101 (192.168.101.254) and vlan102 |
| port16 | down | 192.168.1.99/24, allowaccess ping https http |
| port2, port5–15, port17–24, ha, modem | down | free |
| lan (hard-switch) | 192.168.100.99/24 | allowaccess ping https ssh fabric |

**Discrepancy with handover:** tenants are on VLANs **150 to 175** (26 VLANs), carried on the 1G LACP bond port3+port4, not on a single 10G port. x1 at 10G carries only vlan70 and the test VLAN. Verify which cable goes to Zyxel switch 101 port 10.

## Admin accounts
Only `mat` is visible (profile super_admin_readonly, trusted hosts 0.0.0.0/0 on all ten slots, two-factor disabled). No super_admin account appears in `show system admin` or the full config from this account, so a read-only profile is likely hiding others. Full admin needs the console (lead not detected on the jump box USB bus).

## Policy summary (31 policies)
- One accept+NAT policy per tenant VLAN to x4, plus vlan70, vlan200-TEST and x1 to x4.
- Inbound: x4 → vlan151 via VIP, x4 → vlan161 ("internet -> Vlan161").
- VIPs: 193.221.131.34 → 192.168.161.250; 193.221.131.33 → 192.168.151.254 (named "-disabled").
- SSL-VPN policy ssl.root → vlan101.

## Lockdown-phase findings (not touched)
1. **HTTPS admin is enabled on the WAN interface x4** (`allowaccess ping https`) with no trusted-host restriction on the visible admin. Public exposure of the GUI.
2. port16 (down) and vlan101 allow plain HTTP admin.
3. Admin trusted hosts are 0.0.0.0/0.
4. DNS is 8.8.8.8 / 8.8.4.4; central management is FortiGuard; no syslog server configured.
