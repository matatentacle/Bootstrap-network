# Switch layer - discovery 14 Oct 2026

Read-only. Sources: SSH to the 14 GS1920s with the Nebula local admin account
(`~/jumpbox-setup/zyxel-sw-cmd.sh`), outputs in raw/ (system-information, lldp info remote,
vlan, trunk, interfaces status, mac address-table, running-config per switch), plus the ATP500
DHCP/ARP tables and the FortiGate ARP table. All Zyxel kit is Nebula-managed (cloud ACLs present
in every running-config). Nebula device names (e.g. "SW01") are NOT the switch system names.

## Topology (LLDP, confirmed by MAC tables)

    ATP500 LAN1 (ge4) -------- 1G trunk, all tenant VLANs ------> SW01 port 2
    FortiGate LAN-Bond-2 (port3+port4) --- LACP 2x1G ----------> SW01 ports 9+10 (trunk group T1, active)

    SW01 = 192.168.1.39  GS1920-24HP  sysname "GS1920"  (CORE; Nebula name SW01)
     |- p23 --> 192.168.1.38  GS1920-24HP "GS1920"  (second hub)           p23
     |    |- p25 --> 192.168.1.44  GS1920-24HP "GS1920"                    p25
     |    |    |- p23 --> 192.168.1.43  GS1920-24HP "GS1920"               p23
     |    |    '- p24 --> 192.168.1.42  GS1920-24HP "GS1920"               p23
     |    |- p26 --> 192.168.1.34  GS1920-24HP "GS1920"                    p25
     |    |    '- p23 --> 192.168.1.40  GS1920-24HP "GS1920"               p23
     |    |         '- p8 --> Cisco Small Business "switch8a8c4d" 192.168.16.14 (vlan16)
     |    |- p27 --> 192.168.1.36  GS1920-24HP "GS1920"                    p25
     |    |- p28 --> 192.168.1.41  GS1920-24HP "CW2 Second Floor SW05"     p25
     |    |- p2  --> 192.168.1.46  GS1350-6HP  "FITZROY HOUSE FHG2 (SPLITT...)" port1
     |    '- p5  --> TP-Link switch "Main_SW_A8-29-48" port 1/0/12, untagged VLAN 64 (tenant-owned)
     |- p25 --> 192.168.1.33  GS1920-24HP "PH3 Third Floor SW12"           p25
     |    '- p24 --> 192.168.1.45  GS1920-24HP "PH3 Third Floor SW13"      p23
     |- p26 --> 192.168.1.35  GS1920-24HP "PH2 Second Floor SW04"          p25
     |- p27 --> 192.168.1.47  GS1920-24HP "PH1 First Floor SW03"           p25
     '- p28 --> 192.168.1.37  GS1920-8HP  "GS1920"                         p9
          '- p1 --> 192.168.46.4  GS1350-6HP "GS1350" (vlan46)

Not placed: Cisco "switch6cb4d5" 192.168.16.13 (no LLDP sighting; probably behind the other Cisco).
Every inter-switch link is a single 1G copper or SFP link. The only LAG anywhere is SW01 T1 to the
FortiGate. Deepest path is 4 hops (SW01 > .38 > .44 > .42/.43). No ring, no redundancy.

Evidence for the ATP500 on SW01 port 2: ATP500 LAN-side MACs (d8:ec:e5:bf:dc:xx) are learned on
SW01 port 2 and on every other switch's uplink port; port 2 has been up 525 h, the same as ATP500 port 4.
FortiGate: LLDP from SW01 p9/p10 shows FW-120G-01 port4/port3; only the bond MAC 78:18:ec:f2:6b:ce/cf
appears in any switch table. FortiGate x1 (192.168.201.0/24, hosts .2-.5 incl. two 80:ea:0b Zyxel
units and 08:92:04:0a:74:c0) is NOT on this fabric and is unreachable from the jump box.

## Inventory
| IP | Model | System name | MAC | Firmware | Uptime 14 Oct |
|---|---|---|---|---|---|
| 192.168.1.33 | GS1920-24HP | PH3 Third Floor SW12 | bc:cf:4f:bb:d8:b3 | V5.00(ABMI.3) | 4091 h |
| 192.168.1.34 | GS1920-24HP | GS1920 | bc:cf:4f:bb:e4:7b | V5.00(ABMI.3) | 4090 h |
| 192.168.1.35 | GS1920-24HP | PH2 Second Floor SW04 | bc:cf:4f:bb:c8:f4 | V5.00(ABMI.3) | 4091 h |
| 192.168.1.36 | GS1920-24HP | GS1920 | bc:cf:4f:bb:cb:55 | V5.00(ABMI.3) | 4090 h |
| 192.168.1.37 | GS1920-8HP | GS1920 | bc:cf:4f:ce:00:92 | V5.00(ABKZ.3) | 4090 h |
| 192.168.1.38 | GS1920-24HP | GS1920 | bc:cf:4f:bb:e6:85 | V5.00(ABMI.3) | 525 h |
| 192.168.1.39 | GS1920-24HP | GS1920 (Nebula: SW01, core) | bc:cf:4f:bb:ca:e1 | V5.00(ABMI.3) | 525 h |
| 192.168.1.40 | GS1920-24HP | GS1920 | bc:cf:4f:bb:e6:2e | V5.00(ABMI.3) | 4090 h |
| 192.168.1.41 | GS1920-24HP | CW2 Second Floor SW05 | bc:cf:4f:bb:e3:76 | V5.00(ABMI.3) | 4091 h |
| 192.168.1.42 | GS1920-24HP | GS1920 | bc:cf:4f:c4:bc:90 | V5.00(ABMI.3) | 4090 h |
| 192.168.1.43 | GS1920-24HP | GS1920 | bc:cf:4f:c4:bf:48 | V5.00(ABMI.3) | 4090 h |
| 192.168.1.44 | GS1920-24HP | GS1920 | bc:cf:4f:c4:bb:e2 | V5.00(ABMI.3) | 4090 h |
| 192.168.1.45 | GS1920-24HP | PH3 Third Floor SW13 | bc:cf:4f:bb:c4:a6 | V5.00(ABMI.3) | 4091 h |
| 192.168.1.46 | GS1350-6HP | FITZROY HOUSE FHG2 (per LLDP) | bc:cf:4f:5a:7b:9b | not read (login refused) | - |
| 192.168.1.47 | GS1920-24HP | PH1 First Floor SW03 | bc:cf:4f:bb:ca:16 | V5.00(ABMI.3) | 4091 h |
| 192.168.46.4 | GS1350-6HP | GS1350 (per LLDP) | bc:cf:4f:5a:80:e2 | not read (login refused) | - |
| 192.168.16.13 | Cisco Small Business | switch6cb4d5 | 68:86:a7:6c:b4:d5 | - | web only, no SSH |
| 192.168.16.14 | Cisco Small Business | switch8a8c4d | c8:00:84:8a:8c:4d | - | web only, no SSH |

SW01 and .38 (the two hubs) have 525 h uptime, the rest about 4090 h: the two hubs and the ATP500's
LAN port all restarted about 22 Sep 2026. The GS1350 pair refuse the Zyxel admin password (other
local credentials, possibly another Nebula site). Raw LLDP also lists ~55 Zyxel APs (NWA1123, NWA90AX)
and phones per port; see raw/*-show-lldp-info-remote-*.

## VLAN handling - worth checking in Nebula
Each switch's static VLAN table is small (SW01: 1,10,11,34,35,42,101 and 150-175; edge switches 2-14
VLANs each), yet the MAC tables show frames being learned on VLANs that are not in the table
(e.g. SW01 port 2 learns ATP500 MACs on 49 VLANs from 10 to 74). The GS1920s are therefore passing
tagged frames for undefined VLANs across the uplinks. It works, but VLAN isolation on those VLANs
relies on nothing being untagged into them by mistake. Also: VLAN 64 is untagged on .38 port 5 into a
tenant's own TP-Link switch.


## Nebula cross-check (device list pasted by Mat, 14 Oct 2026)
Nebula lists 21 Zyxel switches. Mapping Nebula name -> what I found:

| Nebula name | MAC | LAN IP | Cloud exit | Model | Found by me |
|---|---|---|---|---|---|
| 2.18 Ground Floor SW01 (main comms) | bc:cf:4f:bb:ca:e1 | 192.168.1.39 | ATP500 | GS1920-24HP | yes, CORE |
| 2.18 Ground Floor SW02 (main comms) | bc:cf:4f:bb:e6:85 | 192.168.1.38 | ATP500 | GS1920-24HP | yes, hub 2 |
| PH1 First Floor SW03 | bc:cf:4f:bb:ca:16 | 192.168.1.47 | ATP500 | GS1920-24HP | yes |
| PH2 Second Floor SW04 | bc:cf:4f:bb:c8:f4 | 192.168.1.35 | ATP500 | GS1920-24HP | yes |
| CW2 Second Floor SW05 | bc:cf:4f:bb:e3:76 | 192.168.1.41 | ATP500 | GS1920-24HP | yes |
| 4.09 Second Floor SW06 | bc:cf:4f:bb:e4:7b | 192.168.1.34 | ATP500 | GS1920-24HP | yes |
| 4.09 Second Floor SW07 | bc:cf:4f:bb:e6:2e | 192.168.1.40 | ATP500 | GS1920-24HP | yes |
| 5.47 Third Floor SW08 (rm309) | bc:cf:4f:bb:cb:55 | 192.168.1.36 | ATP500 | GS1920-24HP | yes |
| 5.11 Third Floor SW09 | bc:cf:4f:c4:bb:e2 | 192.168.1.44 | ATP500 | GS1920-24HP | yes |
| 5.11 Third Floor SW10 | bc:cf:4f:c4:bc:90 | 192.168.1.42 | ATP500 | GS1920-24HP | yes |
| 5.11 Third Floor SW11 | bc:cf:4f:c4:bf:48 | 192.168.1.43 | ATP500 | GS1920-24HP | yes |
| PH3 Third Floor SW12 | bc:cf:4f:bb:d8:b3 | 192.168.1.33 | ATP500 | GS1920-24HP | yes |
| PH3 Third Floor SW13 | bc:cf:4f:bb:c4:a6 | 192.168.1.45 | ATP500 | GS1920-24HP | yes |
| 5.16 Third Floor SW14 | bc:cf:4f:bb:c4:6c | 192.168.201.4 | FortiGate | GS1920-24HP | no: on the FortiGate x1 island |
| 1.24 Basement SW15 | bc:cf:4f:ce:00:92 | 192.168.1.37 | ATP500 | GS1920-8HP | yes |
| Bar Switch SW16 | bc:cf:4f:5a:80:e2 | (192.168.46.4) | ATP500 | GS1350-6HP | seen; login refused; Nebula says not up to date |
| Roof Bar SW/01 SW17 | bc:cf:4f:5a:75:90 | - | 185.53.226.147 (third WAN) | GS1350-6HP | no: not on this fabric, separate internet |
| Roof Bar SW/02 SW18 | bc:cf:4f:53:f8:c9 | 0.0.0.0 | offline | GS1350-6HP | no: offline in Nebula |
| SW101 | 80:ea:0b:25:b1:d6 | 192.168.201.2 | FortiGate | XS1935-12F (10G SFP+) | no: FortiGate x1 island |
| SW102 | 80:ea:0b:25:b1:66 | 192.168.201.3 | FortiGate | XS1935-12F (10G SFP+) | no: FortiGate x1 island |

Resolved: "Zyxel switch 101 port 10" in the handover is SW101, an XS1935-12F on the FortiGate x1
side (192.168.201.2). The FortiGate's 10G x1 most likely lands on SW101 port 10. That island
(SW101, SW102, SW14) is the new 10G fabric; it reaches Nebula through the FortiGate WAN
(193.221.132.138), everything else goes out via the ATP500 WAN (157.231.154.206).

Seen by me but NOT in Nebula: 192.168.1.46 GS1350-6HP bc:cf:4f:5a:7b:9b "FITZROY HOUSE FHG2 (SPLITT...)",
on SW02 port 2. Different org/site or standalone; explains the refused password. Bar Switch SW16 is in
Nebula but also refused the password; it is flagged "not up to date", so Nebula may not have pushed the
current local credentials to it.

Totals now: 21 Zyxel in Nebula + 1 Zyxel outside Nebula + 2 Cisco = 24 switches. 14 read over SSH.
Nebula name = system name only for SW03/04/05/12/13; the rest still answer as "GS1920".

## Still open
- SW101 port 10: confirm the FortiGate x1 cable lands there (needs access to the x1 island or a look at SW101 in Nebula).
- Local credentials for 192.168.1.46 (not in Nebula) and Bar Switch SW16; Cisco pair models (web login only).
- FortiGate x1 island (SW101, SW102, SW14 on 192.168.201.x): no path from the jump box; Nebula topology view covers it.
