# Curam and ReLine both complain about WiFi: what they share

Checked 23 Oct 2026, read-only. Companion to `curam-wifi-2026-10-23.md`. Mat said ReLine
(FortiGate VLAN 151, FH2.1 and 2.14) complain often too; Curam (VLAN 152, PH2.3) said the WiFi
"has been crap" on 15 Oct and again this week.

## Shared pieces, and what each looked like at 19:40 to 20:00 on 23 Oct

| Shared piece | Checked | Result |
|---|---|---|
| Access point | LLDP on SW04 p12 and SW06 p3 | Both are one Zyxel NWA50AX (entry 2x2 WiFi 6, one Ethernet port): "PH2.3" 192.168.152.18 and "FH2.1WIFI" 192.168.151.10. Each is the tenant's only connection. ReLine's one AP covers two rooms. |
| Edge switch port | counters, PoE | Both 1G full, 0 errors, 0 CRC, PoE class 4 at 4 to 5 W with 350 W spare. Up 387 h (Curam) and 649 h (ReLine). Clean. |
| Path to the FortiGate | SW01 trunk T1 (ports 9+10, LACP) | Active, both members up 244 h (since 13 Oct afternoon, the discovery day), 3 CRC errors on port 9 in that time, 0 on port 10. Utilisation under 1% at 20:00. |
| FortiGate itself | performance status | CPU 4%, 383 sessions, under 1 Mbps. Uptime 31 days. |
| FortiGate NICs | get hardware nic port3/port4/x4 | Link 1G/1G/10G full, no error fields exposed by this account (NP7lite shows packet and byte totals only). |
| WAN | execute ping from the FortiGate | 0% loss, 1 ms to 8.8.8.8 and 1.1.1.1. ATP500 WAN the same. Evening snapshot only. |
| FortiGuard | get system fortiguard | Web filter and antispam contracts valid to 16 Jan 2028; anycast enabled; SDNS over port 853. |
| DHCP | config | Identical servers for 151 and 152: 7-day lease, pool .10 to .250, DNS handed out = 8.8.8.8 / 8.8.4.4. |
| Firewall policy | config | Identical to every other FortiGate tenant: flow UTM with certificate-inspection, webfilter "default", dnsfilter "default", application control "default" (monitor only). |
| Interface caps | show system interface | vlan151 outbandwidth 60000 (sheet 60, matches); vlan152 100000 (sheet 250, low). No inbandwidth on either. |

## The two things that genuinely connect them

1. **One small AP each.** Both tenants run their whole office off a single NWA50AX. The ATP500
   tenants who were checked today (therapy block) had a cap problem, not a radio problem; these two
   have a radio problem. ReLine: two rooms, one AP. Curam: AP on the wrong socket because the AP
   socket is dead. Everything RF (channel, utilisation, 2.4 vs 5 GHz, retries, firmware) is only
   visible in Nebula; open "PH2.3" and "FH2.1WIFI" there side by side.
2. **FortiGate tenants get inspection, ATP500 tenants do not.** None of the 60 ATP500 secure-policy
   rules carries any UTM profile (no app-patrol, content-filter, IDP, AV or SSL inspection).
   Every FortiGate tenant policy does: flow-mode web filter, DNS filter and application control
   with certificate inspection. That is the only gateway-level difference between the people who
   complain and the people who do not. It is not proven to be the cause (licences are valid,
   nothing is set to block), but a DNS filter in the path adds a FortiGuard rating round-trip to
   new lookups, and web filtering plus QUIC inspection changes how browsers behave. Easy test
   when Mat is on site: a laptop on VLAN 151 or 152, time DNS lookups and page loads with the policy
   as is, then with UTM temporarily off on that one policy (a FortiGate change, Mat's call).

## Not a connection

- The FortiGate ARP table shows both APs a second time as 192.168.1.2 (the Zyxel fallback address),
  both aged about 11 to 12 hours at 20:00, so both announced it around 08:00 today, and both did the
  same on 14 Oct. The ATP500 ARP table shows none of its 20-odd Zyxel APs doing this, but the ATP500
  ages entries out within minutes while the FortiGate keeps them for hours, so that is not a fair
  comparison. The switch ports never dropped, so the APs are not rebooting. Worth one look in Nebula
  for anything logged around 08:00; otherwise ignore.
- Switch-port bandwidth limits: SW04 p12 and SW06 p3 both have a rate configured but not enabled
  (dormant, see `switch-port-caps-2026-10-23.md`). Not in play today.
- Physical path: different buildings, different edge switches (SW04 direct to SW01; SW06 via SW02).
  Only SW01 and the FortiGate LAG are common, and both are clean.

## Suggested order

1. Nebula: look at the two APs. If utilisation or retry rates are high, the answer is a second AP
   (or a better-placed one) per tenant, and for Curam the SP11 cable fix first.
2. If Nebula looks fine, do the UTM on/off test on one policy during a quiet hour.
3. Separately: raise vlan152 outbandwidth to 250000 to match the sheet.

## Evidence (private/captures, 23 Oct 19:55 to 19:58)

fortigate/get-system-fortiguard-*, get-system-status-*, execute-ping-8-8-8-8-*, execute-ping-1-1-1-1-*,
show-system-interface-vlan151-*, get-system-arp-*, get-hardware-nic-port3|port4|x4-*,
get-system-interface-physical-*; switch-192.168.1.34/show-interfaces-3-*, show-lldp-info-remote-interface-port-channel-3-*,
show-poe-status-*; switch-192.168.1.39/show-trunk-*, show-interfaces-9|10|2-*; atp500/ping-8-8-8-8-*.
Config: configs/fortigate/full-config-2026-10-13.conf policies 3 (vlan151) at 40775 and 4 (vlan152) at 43096,
DHCP servers 7 and 8 at 30571 and 30611; configs/atp500/running-config-2026-10-13.conf secure-policy 1 to 60 at 3192 on.
Not readable with the read-only FortiGate account: diagnose netlink, diagnose hardware deviceinfo nic,
diagnose test application dnsproxy, diagnose netlink aggregate (all return "Unknown action 0").
