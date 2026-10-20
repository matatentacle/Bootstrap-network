# ATP500 notes — updated 2026-10-13

Management 192.168.254.1 (ge7) from jump box enx503eaacea0c4 (DHCP 192.168.254.100). HTTPS 50483, SSH 22, Google Authenticator 2FA.
Source files: version, cpu, mem, interface-all, dhcp-binding, running-config (4,492 lines), session log.

## Identity
| Item | Value |
|---|---|
| Model | ATP500, hostname atp500 |
| Firmware | V5.43(ABFU.0) built 2026-07-29 running; V5.42(ABFU.1) on standby partition |
| WAN | ge1 157.231.154.206/30; ge1:1 157.125.150.201/29 |
| Tenant VLANs | vlan10–35 and more, all x.x.N.254 on the LAN side (see interface-all) |
| ge7 | 192.168.254.1/24, type internal, DHCP pool Network_Pool_GE7 |

## Admin-type accounts (from running-config)
admin (admin), Shopna (admin), MKennedyAdmin (admin), bootstrapadmin (limited-admin), Mat-Kennedy (limited-admin). Hashes only in the repo.
Added by Mat 14 Oct 2026: read-only (limited-admin, no 2FA) for the jump box scripts; password in ~/jumpbox-setup/.env on MINI-PC-6, not here.

## Jump box DHCP reservation
Not in place. Binding for 50:3e:aa:ce:a0:c4 is 192.168.254.100, reserve=no, lease to 2036-10-10. Handover expected .10.

## Known quirks logged for the lockdown phase (not touched)
- Weekly reboot: `schedule reboot weekly 04:00 mon`
- Cloud-helper auto firmware update with reboot: `weekly sun 0 reboot yes`
- Policy 3 "Webaccess" allow-any shadows later denies (per handover; policy section in running-config)
- Management services accept from every zone (per handover)
