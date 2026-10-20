---
name: switch-layer
description: Bootstrap switch fabric as mapped 14 Oct 2026 - SW01 core, 18 switches, Nebula-managed, what still needs creds
metadata:
  type: project
---

Mapped 14 Oct 2026 by LLDP over SSH (notes: /srv/configs/switches/NOTES.md, report: ~/jumpbox-setup/SWITCH-MAP-2026-10-14.txt). Core is SW01 = 192.168.1.39 (GS1920-24HP, system name still "GS1920"): ATP500 LAN1 trunk on port 2, FortiGate LAN-Bond-2 LACP on ports 9+10, downstream on 23 and 25-28; 192.168.1.38 is a second hub. 24 switches in all: 21 Zyxel in Nebula (Nebula names SW01-SW18, SW101, SW102; SW01=.39, SW02=.38), one GS1350 at 192.168.1.46 outside Nebula, 2 Cisco Small Business (vlan16). The FortiGate x1 island is SW101 and SW102 (XS1935-12F 10G) plus SW14 at 192.168.201.2-.4. All links single 1G, no redundancy, chains up to 4 deep. FortiGate x1 (192.168.201.x) is a separate fabric the jump box cannot reach. Switches pass tagged frames for VLANs not in their VLAN tables (check in Nebula).

**Why:** Mat wants local read access to the switches during the ATP500 to FortiGate migration; everything Zyxel is Nebula-managed, so control lives in Nebula, not SSH.
**How to apply:** Use ~/jumpbox-setup/zyxel-sw-cmd.sh with the "Zyxel" section of .env; read-only commands only. Still blocked: GS1350s at .46 (not in Nebula) and SW16 refuse that password, Cisco pair have no SSH, "switch 101 port 10" from the handover is SW101 (XS1935-12F on the FortiGate x1 side), still unconfirmed which port. Related: [[bootstrap-jumpbox]], [[read-only-no-permission]], [[gateway-working-rules]].
