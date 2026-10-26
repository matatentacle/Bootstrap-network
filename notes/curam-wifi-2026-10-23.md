# Curam (PH2.3, FortiGate VLAN 152): "WiFi is really bad"

Fault-finding 23 Oct 2026, read-only (FortiGate read-only account, SW04 over SSH, 13/14 Oct
captures, Bootstrap workbook). Nothing changed. Patrick (Curam) had already said "the WiFi has
been crap" on 15 Oct in the External IP Check thread.

## What Curam actually have

- One access point, a Zyxel NWA50AX (entry-level 2x2 WiFi 6, single Ethernet port), Nebula name
  "PH2.3", MAC f4:4d:5c:fa:6a:87, DHCP 192.168.152.18. It is the only thing plugged in for Curam.
- It sits on SW04 (PH2 Second Floor, 192.168.1.35) port 12, PVID 152 untagged. Link 1G full,
  up 387 h (since about 7 Oct 16:30), 0 errors, 0 CRC, 0 runts, PoE class 4 drawing 4.1 W with
  352 W spare on the switch. The port is clean.
- Workbook row for Curam PH2.3: ports "11 - (AP) / 12 (LAN) / 14 active", wall ports
  "33-SP12 / 34-SP11/14 cable issues". On the switch, ports 11 and 14 are administratively
  `inactive` and down. So the AP wall socket (SP11) and the spare (SP14) are dead because of the
  recorded cable fault, and the AP has been put on the LAN wall socket (SP12) instead. With an
  NWA50AX there is no second port, so Curam have no wired LAN at all: every device is on one small AP
  wherever the LAN socket happens to be, which is probably not where an AP belongs.
- Clients seen on VLAN 152: about 8 to 10 (14 Oct ARP had 9 entries, 23 Oct evening 7), mostly
  Apple and randomised-MAC phones/laptops. One device (bc:f1:05:9f:ae:5c) holds two addresses
  (.38 plus a DHCP one), so something has a static IP inside the DHCP pool .10 to .250.

## FortiGate side (not the cause, but noted)

- vlan152: outbandwidth 100000 kbps (100M download cap), inbandwidth 0 (no upload cap). Sheet says
  250 Mbps. Mismatch, already in the crossref bandwidth-check.
- Policy 4 (vlan152 -> x4, all) has the same inspection set as every other tenant VLAN:
  certificate-inspection, webfilter default, dnsfilter default, application-list default (monitor
  only). Policy 35 whitelists *.ecare123.site ahead of it. Nothing Curam-specific.
- FortiGate load at 19:43: CPU 4%, 383 sessions, under 1 Mbps average. DHCP: 7-day lease, pool
  .10 to .250, DNS handed out = system DNS 8.8.8.8 / 8.8.4.4.
- The FortiGate ARP table shows the AP's MAC a second time as 192.168.1.2 on vlan152 (also on
  14 Oct, and the ReLine AP on vlan151 does the same). 192.168.1.2 is the Zyxel AP fallback address;
  both APs announce it, so it is a Zyxel habit, not a Curam fault. Worth a glance in Nebula that the
  AP is not losing DHCP, but the switch port never dropped in 387 h, so it has not been rebooting.

## Likely cause

Coverage and capacity, not the wire: one entry-level AP, in the wrong place (the LAN socket, since
the AP socket is dead), serving the whole office, with ~55 other Zyxel APs in the building on the
same air. The RF side (channel, utilisation, 2.4 vs 5 GHz, band steering, firmware, client
roaming/retries) is only visible in Nebula: open AP "PH2.3", check clients, channel utilisation,
whether it is on 2.4 GHz heavy, and whether Nebula flags it "not up to date".

## What would fix it (for Mat to decide)

1. Fix or re-terminate the SP11 wall cable (workbook: "cable issues") and re-enable SW04 port 11
   with PVID 152, then put the AP back on the AP socket and give Curam the LAN socket back. Or add
   a second AP; the sheet calls Curam a 250 Mbps tenant and they are on one NWA50AX.
2. In Nebula, check "PH2.3": channel plan, 5 GHz preferred, firmware, client count.
3. Raise vlan152 outbandwidth to 250000 to match the sheet (FortiGate change, needs OK).
4. Ask Curam what is at .38 with a static IP, and move it out of the DHCP pool or reserve it.

## Evidence

private/captures/fortigate/show-system-interface-vlan152-20261023-194255.txt
private/captures/fortigate/get-system-performance-status-20261023-194300.txt
private/captures/fortigate/get-system-dns-20261023-194301.txt
private/captures/fortigate/get-system-arp-20261023-*.txt
private/captures/switch-192.168.1.35/show-interfaces-12-20261023-*.txt (counters)
private/captures/switch-192.168.1.35/show-lldp-info-remote-interface-port-channel-12-20261023-*.txt
private/captures/switch-192.168.1.35/show-poe-status-20261023-*.txt
configs/fortigate/full-config-2026-10-13.conf: vlan152 interface 4535-4615, DHCP server 8 at 30611,
policy 35 at 43023, policy 4 at 43096
configs/switches/raw/192.168.1.35-show-running-config-2026-10-14.txt lines 47-53 (vlan 152), 192-247 (ports 11-14)
configs/bootstrap-records/workbook-2026-10-07/BS_config_sheet.csv line 11
Note: "diagnose netlink interface list" and "diagnose hardware deviceinfo nic" return "Unknown action 0"
for the read-only FortiGate account, so interface error counters on the FortiGate side were not read.
