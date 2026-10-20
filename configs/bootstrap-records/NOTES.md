# Bootstrap's own records (their working spreadsheets) — ingested 14 Oct 2026

**What this is.** Bootstrap's "VLANs and Configurations" workbook is *their* record of the tenant
network, kept by hand since 2021. It is the closest thing that exists to a statement of what they
think is set up and what they intend for the migration. It is not our target state. We consume it,
check every claim against the device captures, and pull their margin notes out as intent signals.
Treat anything here that has not been verified against a device as a claim.

## Provenance
| Item | Source | Drive ID | Last modified |
|---|---|---|---|
| workbook-2026-10-07/ | Shared drive "Bootstrap" root > "2. VLANs and Configurations" (.xlsx) | 1B7f9t3k-GedYiUYD-l51Kq8HGOty4n2w | 7 Oct 2026 |
| workbook-2025-12-01/ | Mat's folder A254_BStrap > "VLANS_NAT 01.12.25.xlsx" (earlier copy of the same workbook) | 1GvfdEGxFRDayDnjCu_R0evwOq_XhVY9f | 12 Dec 2025 |

Shared drive folder: https://drive.google.com/drive/folders/0AO-R8iXcHrdqUk9PVA

Each workbook directory has the original .xlsx plus one CSV per tab (exported with tools/xlsx2txt.py;
Excel stored every number as a float, so "5.0" means port 5, and several port cells were auto-converted
to dates: "2025-06-01 00:00:00" was typed as "1/6", i.e. ports 1 and 6).

**Not retrievable through the Drive connector (check in a browser):**
- "1. ORDERS TO ACTION: Broadband Tenant Orders (Form Responses)" — a shortcut; target not accessible.
- Archive > "2. INSTALL & RECORD: Configuration Record" — a shortcut; target not accessible.
- Folders "Network Diagrams" and "Troubleshooting References" listed as empty via the API.
- "Bootstrap Broadband Order form" is a Google Form (the intake form that feeds the orders sheet).

## Tabs in the 7 Oct 2026 workbook
| Tab | Rows | What it is |
|---|---|---|
| BS config sheet | 99 | One row per tenant/room: org, building, room, speed, switch, switch port, room port, VLAN, ticket, notes. The tenant register. Rows go back years; stale rows are not deleted, so one port can appear under three tenants. |
| VLANs - ATP500 | 64 | VLAN 10–74: status (Active / Inactive / MAKE SHARED), name, gateway IP, bandwidth, public IP, notes. Unchanged since Dec 2025 except two notes. |
| VLANS - FORTIGATE | 12 | VLAN 150–161 on the FortiGate: client, bandwidth. Grew by 158–161 since Dec 2025. Header: Vorboss line, 193.221.132.138, secondary 193.221.131.32/27. |
| Routing-Public IP | 10 | ATP500 policy routes: which VLAN SNATs to which 157.231.128.x. Pasted from the ATP500 GUI. |
| NAT | 14 | ATP500 virtual servers / 1:1 NAT, with "Move NATS to Fortigate" written underneath. |
| 1-1 SNAT, LOOPBACK SNAT, SNAT STATUS | — | More ATP500 GUI pastes of the same NAT rules. |
| Policy control 091025 | 50 of 90 | ATP500 firewall rules as of 9 Oct 2025, page 1 of 2 only. |

## Cross-reference outputs (crossref-2026-10-14/)
Produced by tools/crossref.py from the CSVs plus the device captures already in this repo
(atp500/running-config-2026-10-13.conf, interface-all, dhcp-binding and arp-table of 14 Oct;
fortigate/full-config-2026-10-13.conf and arp-2026-10-14.txt; switches/raw/*-show-running-config-2026-10-14.txt
for the 14 GS1920s read over SSH). Re-run after a fresh capture:

    python3 -I tools/crossref.py workbook-2026-10-07 /srv/configs crossref-<date>

| File | Content |
|---|---|
| vlan-register.csv/.txt | One row per VLAN seen anywhere (94): sheet status/name/bandwidth/public IP, device description/IP/state, DHCP leases and ARP entries on 14 Oct, bandwidth rule, SNAT, FortiGate policies, switch access ports, config-sheet tenants, flags. |
| port-check.csv/.txt | Every config-sheet row's switch/port/VLAN claim against the switch running-config. |
| undocumented-ports.txt | Access ports carrying a tenant VLAN that no sheet row claims. |
| public-ip-register.txt | 157.231.128.130–.142: device policy route + NAT vs the sheet. |
| bandwidth-check.txt | Sheet bandwidth column vs device rule, differences only. |
| intent-notes.csv/.txt | Their margin notes, per VLAN, tagged (MOVED-TO-FORTIGATE, FREE-REUSABLE, TENANT-LEFT, HAS-NAT, STATIC-IP, MAKE-SHARED, FIX-AT-VORBOSS-MOVE, ...). |

## Headline findings (14 Oct 2026)
Port claims: 103 rows; 58 match the switch exactly, 4 partly, 18 contradict it, 23 cannot be checked
(no switch/port given, or the switch is one we could not read: SW16 bar switch, the FHG2 GS1350, SW14 on the
FortiGate x1 island). Nearly every contradiction is a stale row that was never deleted when the tenant moved;
in each case a newer row for the same port is right. 25 access ports carry a tenant VLAN with no sheet row at all.

Things the sheet gets wrong or leaves out that matter for the migration:
1. **VLAN 70 exists on both gateways** with the same subnet: ATP500 vlan70 192.168.70.254 (6 DHCP leases, SW05 p12)
   and FortiGate vlan70 on x1, alias LeadersUnlocked, 192.168.70.254 (1 ARP). The sheet only knows the ATP500 one.
2. **VLAN 48 Field Vision** is "Inactive / left, can be reused" on the sheet but had 21 DHCP leases and four switch
   ports (SW09 p3/4/6, SW12 p20) on 14 Oct — "left but APs active". Not free.
3. **VLAN 11 Curam** "moved to FortiGate vlan151", yet the ATP500 still policy-routes it to 157.231.128.131 and SW01 p20
   is untagged 11. **VLAN 45 Snafu** "left, can be reused" still has SNAT .137, two virtual servers and SW09 p2.
   **VLAN 33 Haberdashery** still has SNAT .133 and a NAS virtual server. Dead public-IP plumbing to drop, not carry over.
4. **VLAN 15** (sheet: Active, Felicity Kay CW208) has no port, no hosts; CW208 is on VLAN 10 now. Dead.
   **VLAN 53** Bridge the Gap: port SW12 p13 assigned, zero hosts on the day.
5. **VLAN 72 Ashford has no bandwidth rule**: ATP500 bwm 4 is named Vlan72_AshfordSons but applies to vlan73, so
   vlan73 (Civil Society) has two rules (30M + 100M) and vlan72 is uncapped. bwm 6 "Vlan60_LeaderUnlocked" is on vlan70.
6. **Bandwidth column is unreliable**: 39 differences (bandwidth-check.txt). E.g. VLAN 27 DGN sheet 30M, device 500M;
   VLAN 20 sheet 100M, device 250M; VLAN 39 sheet 100M, device 30M. FortiGate VLANs 153/156/157/159/161 have no cap at all.
7. **FortiGate VLANs 162–175** are built (IP, DHCP, 100M policy each) and are not in the sheet: a spare pool of 14.
   VLAN 101/102 on port1 and vlan200-TEST are not in the sheet either.
8. **VLAN 161 Mediorite**: sheet says Active 500M and also "set up by Asim for FF on NAT - not needed". Device: VIP
   193.221.131.34 -> 192.168.161.250 and an inbound policy; VLAN 161 is tagged on Mediorite's port SW03 p7 alongside
   untagged 58; no ARP on 14 Oct. Needs Bootstrap to say which it is.
9. **VLAN 59 Full Time Hobby** (11 leases) and **VLAN 67 Silverfish** at FHG2 reach the ATP500 through SW02 p2, which
   does not carry 59 or 67 in its VLAN table (untagged 1, tagged 10,27,40,64,65,71). They work only because the GS1920s
   forward tags for undefined VLANs. Same for VLAN 40 ACS (tagged on SW02 p4, untagged nowhere we can see).
10. **VLAN 31 Lickerish**: 1:1 NAT to 157.231.128.135 with no policy route and no hosts; sheet says "??". VLAN 47
    "Duplicate for LAWA?" and VLAN 65 Dusty Knuckle R2 (SW02 p6, 200M rule, no hosts) are also unexplained by them.
11. Public IPs: device and sheet agree on .130–.140. .142 is an unused address object; .141 is not defined anywhere.
    Their note under the NAT tab is "Move NATS to Fortigate". Tentacle's .134 is no longer needed (Mat, 14 Oct 2026).
12. SW02 p4 is listed three times (Bootstrap PHG3-5 VLAN10, ACS VLAN40, Dusty Knuckle PHG5 VLAN64); the port is
    untagged 10 + tagged 40,64, i.e. a trunk into a cable run that is then split downstream. Consistent, just recorded three ways.

What their margin notes say they intend (intent-notes.txt): VLAN 13 to become the shared VLAN ("CHANGE THOSE ON VLAN 1 TO
VLAN 13"); VLAN 10 to be split because tenants share it; VLAN 41 Raze/Eat Club to be separated "when moving to vorboss";
VLAN 54 kept as a spare for Thames Reach whose firewall sits on VLAN 39; NATs to move to the FortiGate; VLANs
22, 23, 25, 29, 30, 33, 43, 45, 48, 61 marked reusable (48 is not, see above); 11, 19 already moved to the FortiGate.
