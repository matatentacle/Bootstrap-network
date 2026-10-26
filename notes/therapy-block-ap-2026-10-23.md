# Therapy block WiFi slow after new AP (Ryan, 22 Oct 2026)

Fault-finding on 23 Oct 2026. Read-only: ATP500 and SW12 live reads via bin/jb, plus the
13/14 Oct captures. Nothing changed.

## The report

Ryan forwarded Nick Corrigan (nickcorrigantherapy.com), 21 Oct 18:14: speed test next to the new
AP in Krysh's room (PH 3.10B, SSID Ph310B-THR) is much slower than the old connection, upload
especially poor, worried about several video calls at once. The old connection was a piggyback
on Bootstrap Newton Dunbar's WiFi (PH3.2, VLAN 10). Ryan plans to switch the old one off Monday.

## What is actually there

- New AP: Zyxel, hostname "PH3", 192.168.13.10, MAC d4:1a:d1:58:d3:7b, DHCP lease on vlan13.
  Two client devices seen (iPhone .18, iPad .19).
- Switch: SW12 (PH3 Third Floor, 192.168.1.33) port 2, PVID 13, link up since about 17:40 on
  21 Oct (49 h 14 m at 18:55 on 23 Oct). Port has a per-port limit of 60,000 kbps in and out.
  VLAN 13 was added to SW12 about 7 Oct (164 h old on 14 Oct).
- Gateway: ATP500 interface vlan13 (Vlan13_BootstrapCR, 192.168.13.254/24), active.
- Old connection for comparison: Newton Dunbar is SW12 port 1, PVID 10, port limit 100M.

## The cause

ATP500 bandwidth management is on (show bwm activation: yes). Rule 57, Vlan_13_BootstrapCR,
vlan13 -> ge1, is active with:

    Inbound  (download) 40,000 kbps, no excess, ceiling 0
    Outbound (upload)   10,000 kbps, no excess, ceiling 0

No excess and no ceiling means the guaranteed figure is also the maximum: VLAN 13 gets about
39 Mbps down and 9 Mbps up, full stop, shared by everyone on the therapy AP. Rule 62 for VLAN 10
(the old Newton Dunbar connection) is 100,000/100,000, so Nick's old speed test would have shown
roughly ten times the upload. Two or three concurrent video calls at 3 to 4 Mbps up each will
saturate 9 Mbps, which is exactly what Nick is worried about.

Bootstrap's workbook has "Print House Therapy, PH 3.10B, 60 Mbps, VLAN13", and the switch port is
already set to 60M each way, so the ATP500 rule is the odd one out (crossref bandwidth-check
already flagged VLAN 13: sheet 100, device 39M). The 40/10 values are probably left over from
whatever VLAN 13 was used for before.

## Fix (needs Mat's OK, it is a change on a production gateway)

Raise bwm 57 to match the sheet: inbound 60000, outbound 60000 (or 100000/100000 like VLAN 10
if the therapy block is to be treated as Bootstrap's own shared space). Switch port 2 on SW12
caps at 60M either way, so anything above 60000 on the ATP500 also needs the Nebula port limit
raised. One rule edit, no reboot. Afterwards re-test with Nick before the old SSID is switched off.

Not the cause: the AP, the WiFi link, the number of users. The speed test was right next to the
AP and the cap sits upstream on the gateway.

## Evidence

private/captures/atp500/show-bwm-activation-20261023-185602.txt
private/captures/atp500/show-bwm-all-20261023-185604.txt (index 57, 62)
private/captures/atp500/show-interface-vlan13-20261023-185605.txt
private/captures/atp500/show-ip-dhcp-binding-20261023-*.txt, show-arp-table-20261023-*.txt
private/captures/switch-192.168.1.33/show-interfaces-status-20261023-185527.txt
private/captures/switch-192.168.1.33/show-mac-address-table-port-2-20261023-185622.txt
configs/atp500/running-config-2026-10-13.conf lines 4257-4262 (bwm 57), 4292-4297 (bwm 62)
configs/switches/raw/192.168.1.33-show-running-config-2026-10-14.txt lines 69-100 (ports 1, 2)
