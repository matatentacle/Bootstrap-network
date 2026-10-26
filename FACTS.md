# Bootstrap network: fact sheet and index

Updated 2026-10-26 by Claude Code: FortiGate outage since 24 Oct and its support-cover facts
(FortiGuard contracts to Jan 2028, registration held by Asim). Earlier basis: the device captures
of 13 and 14 Oct 2026, the notes in this repo, the 23 Oct planning session (tenant replies and
migration plan v2), live reads on 23 Oct for the therapy block WiFi fault, and the cutover
runbook, generated CLI and tenant letters for 27 Oct. Short answers live here; the index at the bottom says where the detail is.
If something here looks wrong or stale, say so and ask before changing it; Claude Code keeps
this file current after each new capture.

Trust order for a fact: device capture (`configs/*`) > this sheet > Bootstrap's workbook
(`configs/bootstrap-records/`, their record, not target state).

## The two gateways

| | ATP500 (retiring) | FortiGate-120G (replacing it) |
|---|---|---|
| Make / firmware | Zyxel ATP500, ZLD V5.43(ABFU.0) | Fortinet FortiGate-120G, FortiOS 7.4.12, serial FG120GTK24015905, hostname FW-120G-01 |
| Tenants | about 44 live, VLANs 10 to 74 | 11 configured on VLANs 150 to 160, 10 with hosts on 14 Oct (155 CoLab empty); 161 Mediorite prepared, no hosts; 14 pre-built spares (162 to 175) |
| Tenant VLAN range | 10 to 74, gateway 192.168.N.254 | 150 to 175, gateway 192.168.N.254, on aggregate LAN-Bond-2 (port3+port4, 2x1G LACP) to SW01 ports 9+10 |
| WAN | ge1 157.231.154.206/30 (old Vodafone line); ge1:1 157.125.150.201/29 referenced by nothing | x4 (10G) Vorboss 193.221.132.138/29, default gateway .137; secondary block 193.221.131.32/27 |
| Public IPs for tenants | routed block 157.231.128.128/28, usable .130 to .142 (see VLAN table) | 193.221.131.33 (ReLine VIP, disabled), 193.221.131.34 (Mediorite VIP, no hosts yet) |
| LAN trunk | ge4 (LAN1) 1G to SW01 port 2 | LAN-Bond-2 to SW01; x1 (10G) 192.168.201.1/24 goes to the separate 10G island (SW101, SW102, SW14) and carries vlan70 + vlan200-TEST |
| Management | 192.168.254.1 on ge7, HTTPS port 50483, SSH 22; Google Authenticator 2FA on full admins | 192.168.10.99 on mgmt, HTTPS 443, SSH 22; HTTPS admin also open on WAN x4 (lockdown item). To move to 192.168.5.0/24 (decided 23 Oct 2026, not yet done) because it overlaps ATP500 VLAN 10 |
| Admin accounts | admin, Shopna, MKennedyAdmin (full); bootstrapadmin, Mat-Kennedy, read-only (limited) | mat (super_admin with 2FA since 20 Oct 2026, Mat's own); ro-jumpbox (super_admin_readonly, trusted hosts = jump box only, no 2FA) created 23 Oct 2026 and used by the jump box scripts; proven with a read the same day |
| HA | none | standalone |
| Scheduled | weekly reboot Mon 04:00; cloud firmware auto-update with reboot Sun | none |
| Support cover | unknown | FortiGuard contracts (web filter, antispam, outbreak prevention) run to 16 Jan 2028, so FortiCare is very likely in force to then, but the level is unconfirmed. Hardware warranty (1 year from registration, about Jan 2025) has lapsed. Registered to Asim Tahir's FortiCloud account (asim@mitsuk.com), not Bootstrap's; "the licence is with Asim" (Shopna, 26 Oct 2026). Part number P28808-04. Detail: `notes/fortigate-outage-2026-10-26.md` |

**Outage, 24 to 26 Oct 2026:** the FortiGate was down from the mains dip at 15:09Z Sat 24 Oct
(PWR on, STATUS off, no ARP; a power cycle at 10:44Z Mon did not clear it) until about 13:04Z Mon
26 Oct, when it booted and all ports, WAN and tenants came back. About 46 hours without internet for
eight FortiGate tenants and PlanetB. Cause: a wrong-type console lead left in the console port
answered the BIOS "press any key" prompt on every boot and held the unit in the BIOS menu; Mat
unplugged it and it booted. Not a hardware fault. Rule: never leave a console lead on the FortiGate
unattended. Detail: `notes/fortigate-outage-2026-10-26.md`.

Known duplicate: VLAN 70 (192.168.70.0/24) exists on both gateways with the same subnet. On the
ATP500 it is Leaders Unlocked; on the FortiGate (x1) it serves PlanetB via SW14 in FHG and its
alias "LeadersUnlocked" is stale (Mat, 23 Oct 2026). FortiGate VLANs 101/102 (port1, down) and
vlan200-TEST are relics with no users.

## Switch fabric (mapped 14 Oct 2026)

- 24 switches: 21 Zyxel in Nebula, 1 Zyxel GS1350 outside Nebula (192.168.1.46, FHG2), 2 Cisco Small Business (VLAN 16, web only).
- Core is SW01 = 192.168.1.39 (GS1920-24HP). Second hub SW02 = 192.168.1.38. Nebula names SW01 to SW18 are not the system names of the switches; most still answer "GS1920". Map: `configs/switches/NOTES.md`.
- All inter-switch links single 1G, no redundancy, chains up to 4 deep. Only LAG is SW01 T1 to the FortiGate.
- 10G island on FortiGate x1: SW101 (192.168.201.2) and SW102 (.3), both XS1935-12F, plus SW14 (.4, GS1920-24HP in FHG, address by DHCP from x1 on VLAN 1). Not reachable from the jump box; Nebula sees it (Mat is negotiating Nebula API access, 23 Oct 2026). FortiGate x1 lands on SW101 port 10; SW101 port 1 is the singlemode run to SW14 (Mat, 23 Oct 2026).
- GS1920s forward tagged frames for VLANs not in their VLAN table (VLANs 40, 59, 67 depend on this).

## Jump box

MINI-PC-6, Ubuntu 22.04, terminal only. Tailscale 100.83.139.20, user tentacle. USB NIC to
ATP500 ge7 (192.168.254.100 by DHCP, the only leg with internet); onboard NIC to FortiGate mgmt
(192.168.10.98 static). Advertises 192.168.254.0/24 and 192.168.10.0/24 to the tailnet. Live
document: `jumpbox-setup/README.md`. Read-only on everything it touches. FortiGate console lead on the box
since 26 Oct 2026 (PL2303, /dev/ttyUSB0, 9600 8N1, proven); a lead on that port held the FortiGate at its BIOS
menu on 24 to 26 Oct, so pull it before any planned reboot until the reboot-with-lead test is done.

## Migration (plan v2, 23 Oct 2026)

Detail: `notes/migration-plan-v2-2026-10-23.md`. Physical layout and shopping list: the "10G
migration plan" frame on the Bootstrap Miro board (uXjVJ1aoEDY=); cabinet frames there are
history. Hardware: everything on `jumpbox-setup/SHOPPING-LIST-10G-2026-10-14.txt` is bought and on
site (Mat, 23 Oct 2026). Suppliers for anything further: Cable Monkey, Broadband Buyer, FS, Canford;
Ebuyer accepted; no marketplace sellers.

- Backbone: FortiGate x1+x2 20G LACP to SW101 SFP 1+2; SW101 to SW102 10G LAG on ports 11+12;
  new fibre from SW101 SFP 3-6 and SW102 SFP 1-5 to the nine cabinet panels, patched next to the
  existing runs. FHG's singlemode run to SW14 moves from SW101 port 1 to SFP 3. SW01 stays as the
  main comms room switch: interim uplink SW102 copper port 12 to SW01 port 24 over Cat6 during the
  migration, permanent uplink SW102 SFP 6 to SW01 port 25 by fibre once PH3 has left port 25, then
  the SW101/SW102 LAG on 11+12 is activated (Mat, 23 Oct). Vorboss 10G WAN stays on x4. Retire
  SW02 and the ATP500. New aggregate name: LAN-Bond-10G.
- Logical: every tenant VLAN 10 to 99 on the new aggregate. ATP500 VLANs 10 to 74 replicated with
  the same IDs and subnets. FortiGate tenants renumbered 150 to 160 -> 75 to 85, 161 -> 86,
  PlanetB (today on FortiGate vlan70 via x1 and SW14 in FHG) -> 87, spares 88 to 99. Every VLAN 10 to 99 is
  created; active tenants get their client name on the interface, inactive and spare VLANs get no
  name. vlan70 on x1, vlan200-TEST, vlan101, 102 and the fortilink aggregate (x2+x3, no managed
  switches) all go. Everyone NATs to the FortiGate WAN 193.221.132.138 (decided 23 Oct evening, replacing
  the earlier idea of a separate pool for the ATP500 arrivals); own addresses only where asked.
- Order: 0 move mgmt to 192.168.5.0/24; 1 build the LAG and VLANs, test on SW101; 2 tidy Nebula
  VLAN tables, bring up the SW102/SW01 trunk with 75 to 99 only (never 10 to 74); 3 renumber
  FortiGate tenants; 4 re-patch cabinets to SW101/SW102 one at a time, each with 10 to 99 on its
  trunk, old uplink out before the new one in; that is the ATP500 cutover, and VLAN 10 may sit on
  both gateways for the day (Mat, 23 Oct). Cabinet order: FHG, PH3, PH2, PH1, Basement, FH3, FH2,
  CW3, CW2. Retire SW02; 6 power off the ATP500, delete LAN-Bond-2.
- Also decided 23 Oct: ReLine's dead VIP .33 is deleted at lockdown; the generated FortiGate CLI
  lives in a committed `plans/` directory; a short outage for PlanetB and island management while
  x1 is cleared for the LAG is accepted. Still to read off Nebula: PlanetB's ports on SW14.
- Cutover date proposed: Tuesday 27 Oct 2026 (Mat, 23 Oct; tenants asked to confirm by Mon 26 Oct).
  Day doc: `notes/cutover-runbook-2026-10-27.md`. CLI: `plans/2026-10-27/` from
  `plans/gen-fortigate-cli.py` (read `summary.txt` first). Tenant letters: `notes/tenant-comms-2026-10-27/`.
  Public addresses decided by Mat 23 Oct 2026 (in the letters): one shared address for everyone,
  the FortiGate WAN 193.221.132.138 (plain NAT, no pool), unless a tenant asked otherwise: .35 Thames
  Reach, .36 Cafe OTO, .34 Mediorite (unchanged); .33 freed at lockdown, .37 to .62 spare. Generator keeps Mediorite on
  VLAN 58 (VIP .34 repointed to 192.168.58.3) instead of moving them to 86; 86 becomes a spare.
  Management VLAN 1 after the cutover: 192.168.1.0/24 everywhere with the FortiGate as 192.168.1.1
  (replica of ATP500 LAN1 on the aggregate, known switches pinned by MAC); 192.168.201.0/24 is dropped
  and SW101/SW102/SW14 become .101/.102/.114, set in Nebula at the start of the x1 window (Mat, 23 Oct
  evening). FortiGate port16's 192.168.1.99 is cleared first (overlap). The last swap is
  SW01 port 2 out, port 24 Cat6 out, SW102 SFP 6 fibre into SW01 port 25 (pre-configured, no Nebula push).

## Tenants and public IPs: open items

- External-IP fact-finding letters went out 15 Oct 2026 (Ryan sent, Mat cc'd); replies in by 23 Oct. Carry over to the FortiGate: Thames Reach (VLAN54, .136), Cafe OTO (VLAN71, .140), Mediorite (VLAN58 -> vlan161/86, VIP .34 already 1:1). New addresses decided 23 Oct 2026: Thames Reach 193.221.131.35, Cafe OTO .36; everyone else shares the FortiGate WAN 193.221.132.138 after the move; letters with the date (Tue 27 Oct) in `notes/tenant-comms-2026-10-27/`. Not carried: DGN Studio (no), Curam (no, already on vlan152), Lickerish (.135 rule points at empty VLAN31, treat as orphaned), Cake and Reline (no reply, already on FortiGate), Snafu and AO Studio (gone). Detail and build notes: `notes/external-ip-fact-finding.md`.
- Dead public-IP plumbing still on the ATP500 that can go without asking: Tentacle .134, Haberdashery .133/.136 rule, Rapid Eye .139, Curam .131.
- Workbook vs reality, headline gaps: VLAN 70 on both gateways; VLAN 48 "reusable" but live (21 leases); dead SNAT/NAT for VLANs 11, 33, 45, 68; VLAN 72 uncapped (its rule sits on vlan73); FortiGate 162 to 175 spare pool not in the sheet; VLAN 161 Mediorite contradicts itself. Full list: `configs/bootstrap-records/NOTES.md`.
- FortiGate CoLab VLAN 155: the CoLab space no longer exists (Mat, 14 Oct 2026).
- Curam bad WiFi (PH2.3, FortiGate VLAN 152): one Zyxel NWA50AX on SW04 port 12 is their only connection; their AP socket (SW04 port 11) and spare (port 14) are admin-disabled with "cable issues" in the workbook, so the AP sits on the LAN socket and they have no wired LAN. Port and FortiGate are clean. Fix is cabling plus a look at the AP in Nebula; vlan152 is also capped at 100M where the sheet says 250M. Detail: `notes/curam-wifi-2026-10-23.md`.
- Curam and ReLine both complain about WiFi: shared path (SW01 LAG, FortiGate, Vorboss WAN, FortiGuard licences) all clean on 23 Oct. What they share is one NWA50AX each as their only connection, and that FortiGate tenants get flow UTM (web filter, DNS filter, app control, certificate inspection) while no ATP500 secure-policy carries any UTM profile. Next: compare the two APs in Nebula, then a UTM on/off test on one policy. Detail: `notes/fortigate-tenant-wifi-common-threads-2026-10-23.md`.
- Therapy block slow WiFi (Ryan, 22 Oct 2026): the new AP "PH3" (192.168.13.10) went live on VLAN 13 via SW12 port 2 on 21 Oct. VLAN 13 is capped by ATP500 BWM rule 57 at 40,000/10,000 kbps (39M down, 9M up, no burst), while the old shared VLAN 10 is 100M/100M. Fix is to raise rule 57 (sheet says 60M; SW12 port 2 is already limited to 60M each way), which needs Mat's OK. Detail: `notes/therapy-block-ap-2026-10-23.md`.

## People and how to write

- Mat Kennedy: operator. Reads on an old phone: plain text, short, no artifacts or HTML.
- Standard AP for upgrades and new installs: Zyxel NWA90AX Pro (NWA90AXPRO-EU0102F) from Broadband Buyer, the step up from the NWA50AX that Curam and ReLine run on (Mat, 23 Oct 2026). Link and detail: `notes/wap-recommendations-history.md`.
- Shopna: places orders at Bootstrap; also the name of an unexplained full-admin account on the ATP500.
- Asim Tahir (asim@mitsuk.com, support@mitsuk.com, company Mitsuk): set up the FortiGate in Jan 2025 and ran it until the handover to Mat on 19 Oct 2026; holds the FortiCloud registration and licence paperwork. Set up VLAN 161 (per the workbook).
- Tenant letters go out signed "The Bootstrap team" via the Bootstrap office; Mat is not the sender. Tone: three short paragraphs, one concrete detail, one question with a date, no tables (`notes/tenant-comms-tone.md`).
- Tenant names, rooms and ports: the register "2. VLANs and Configurations" on the Bootstrap shared drive (0AO-R8iXcHrdqUk9PVA); a copy with CSVs is in `configs/bootstrap-records/workbook-2026-10-07/`.

## Domain, website and mail (public records, 20 Oct 2026)

bootstrapcharity.com: registrar GoDaddy (contacts masked, expires 22 Nov 2028); DNS zone at
SiteGround via the reseller Two Shoes Hosting; website WordPress on Krystal Hosting; mail on
Google Workspace. DMARC report address points at bootstrap.com, a probable typo. Who holds the
GoDaddy and SiteGround logins is unknown; ask David or Ryan (Ryan, Communications, is the likely
website owner). Detail: `notes/bootstrap-domain-dns.md`.

## Index: where the detail is

| Question | Look in |
|---|---|
| Rules for touching anything | `CLAUDE.md`, `notes/gateway-working-rules.md` |
| FortiGate ports, policies, VIPs, lockdown findings | `configs/fortigate/NOTES.md`; raw: `full-config-2026-10-13.conf`, `show-interface`, `routing-table` |
| ATP500 interfaces, admins, quirks | `configs/atp500/NOTES.md`; raw: `running-config-2026-10-13.conf`, `interface-all-2026-10-14.txt`, `dhcp-binding-2026-10-14.txt` |
| Which switch, which port, topology, Nebula name map | `configs/switches/NOTES.md`, `jumpbox-setup/SWITCH-MAP-2026-10-14.txt` |
| Per-VLAN everything (sheet vs device, leases, ports, SNAT, flags) | `configs/bootstrap-records/crossref-2026-10-14/vlan-register.txt` |
| Public IP by VLAN, NAT rules | `configs/bootstrap-records/crossref-2026-10-14/public-ip-register.txt` |
| Sheet port claims vs switch config | `configs/bootstrap-records/crossref-2026-10-14/port-check.txt`, `undocumented-ports.txt` |
| Intent notes per VLAN from the workbook | `configs/bootstrap-records/crossref-2026-10-14/intent-notes.txt` |
| Tenant letters, who got one, public IP per tenant | `notes/external-ip-fact-finding.md` |
| Migration plan v2 (order, VLAN mapping, mgmt move, open decisions) | `notes/migration-plan-v2-2026-10-23.md` |
| Cutover day doc for 27 Oct 2026 (what to paste when, Nebula steps, cabinet order, rollback) | `notes/cutover-runbook-2026-10-27.md`, `plans/2026-10-27/summary.txt` |
| FortiGate outage 26 Oct 2026: timeline, serial and part number, FortiCare/FortiGuard cover, RMA route | `notes/fortigate-outage-2026-10-26.md` |
| Tenant letters for the cutover (fixed IPs, all tenants, FortiGate tenants) | `notes/tenant-comms-2026-10-27/README.txt` |
| Per-port bandwidth limits on the switches vs firewall caps (legacy, remove as found) | `notes/switch-port-caps-2026-10-23.md` |
| Therapy block slow WiFi (VLAN 13 cap) | `notes/therapy-block-ap-2026-10-23.md` |
| Curam bad WiFi (single AP, dead AP socket, VLAN 152) | `notes/curam-wifi-2026-10-23.md` |
| Curam + ReLine WiFi, what the FortiGate tenants share (UTM, one AP each) | `notes/fortigate-tenant-wifi-common-threads-2026-10-23.md` |
| WAP advice Mat already gave Bootstrap (AP Settings doc Oct 2025, audit list Apr 2026) | `notes/wap-recommendations-history.md` |
| Miro board, physical layout, shopping list | `notes/bootstrap-miro-board.md`, `jumpbox-setup/SHOPPING-LIST-10G-2026-10-14.txt` |
| Jump box state, scripts, open items | `jumpbox-setup/README.md`, `notes/bootstrap-jumpbox.md` |
| Discovery narrative 13 Oct | `jumpbox-setup/DISCOVERY-REPORT-2026-10-13.txt` |
| Domain, DNS, website host, mail (bootstrapcharity.com) | `notes/bootstrap-domain-dns.md` |
| All notes, one line each | `notes/MEMORY.md` |

## VLAN table (device state 13/14 Oct 2026; names from the workbook where the device has none)

Status is the workbook status. Public IP is the ATP500 policy-route SNAT where one exists.

| VLAN | Gateway | Status | Name / client | Gateway IP | Public IP | Note |
|---|---|---|---|---|---|---|
| 10 | ATP500 | Active | Vlan10_BootStrap | 192.168.10.254 | 157.231.128.130 | - |
| 11 | ATP500 | Inactive | Vlan11_Curam | 192.168.11.254 | 157.231.128.131 | inactive, ports still assigned |
| 12 | ATP500 | Inactive | Vlan12_bars | 192.168.12.254 | - | inactive, ports still assigned |
| 13 | ATP500 | MAKE SHARED | Vlan13_BootstrapCR | 192.168.13.254 | - | live since 21 Oct 2026: therapy block AP (PH 3.10B) on SW12 port 2; ATP500 BWM rule 57 caps it at 39M down / 9M up, see `notes/therapy-block-ap-2026-10-23.md` |
| 14 | ATP500 | Active | Vlan14_Tenticle | 192.168.14.254 | 157.231.128.134 | - |
| 15 | ATP500 | Active | Vlan15_InsideJob | 192.168.15.254 | - | active on sheet, no hosts, no access port found |
| 16 | ATP500 | Active | Vlan16_Fair_Finance | 192.168.16.254 | - | - |
| 17 | ATP500 | Active | Vlan17_40tf_Brewery | 192.168.17.254 | - | - |
| 18 | ATP500 | Active | Vlan18_Arnie_Productions | 192.168.18.254 | - | - |
| 19 | ATP500 | Inactive | Vlan19_Cake_Architecture_Ltd | 192.168.19.254 | - | - |
| 20 | ATP500 | Active | Vlan20_Julia_Brenard | 192.168.20.254 | - | - |
| 21 | ATP500 | Active | Vlan21_Compost_Creative | 192.168.21.254 | - | - |
| 22 | ATP500 | Inactive | Vlan22_OfficeS_M | 192.168.22.254 | - | - |
| 23 | ATP500 | Inactive | Vlan23_Wine_Bar_PHB8 | 192.168.23.254 | - | - |
| 24 | ATP500 | Active | Vlan24_Lickerish | 192.168.24.254 | - | - |
| 25 | ATP500 | Inactive | Vlan25_Pango | 192.168.25.254 | - | - |
| 26 | ATP500 | Active | Vlan26_LiveThroughThis | 192.168.26.254 | - | - |
| 27 | ATP500 | Active | Vlan27_DGN_Studio | 192.168.27.254 | 157.231.128.132 | - |
| 28 | ATP500 | Active | Vlan28_SarahDawes | 192.168.28.254 | - | - |
| 29 | ATP500 | Inactive | Vlan29_PaperHouseProjects | 192.168.29.254 | - | inactive, ports still assigned |
| 30 | ATP500 | Inactive | Vlan30_Colourworks | 192.168.30.254 | - | - |
| 31 | ATP500 | - | vlan31_Lickerish | 192.168.31.254 | - | - |
| 32 | ATP500 | Active | Vlan32_10pm_Studio | 192.168.32.254 | - | - |
| 33 | ATP500 | Inactive | Vlan33_HaberdasheryLondon | 192.168.33.254 | 157.231.128.133 | - |
| 34 | ATP500 | Active | Vlan34_SistahSpace | 192.168.34.254 | - | - |
| 35 | ATP500 | Active | Vlan35_NewcomerWines | 192.168.35.254 | - | - |
| 36 | ATP500 | Active | Vlan_36_Neighbourhood_Studio | 192.168.36.254 | - | - |
| 37 | ATP500 | Active | VLAN37_Wazzo_LTD | 192.168.37.254 | - | - |
| 38 | ATP500 | Active | Vlan38_Pinzutu_Films | 192.168.38.254 | - | - |
| 39 | ATP500 | Active | Scoff_Studios | 192.168.39.254 | - | - |
| 40 | ATP500 | Active | Vlan_40_Office_SM | 192.168.40.254 | - | no access port found |
| 41 | ATP500 | Active | Vlan41_The_Raze_Collective | 192.168.41.254 | - | - |
| 42 | ATP500 | Active | Vlan42_FormFormForm_ltd | 192.168.42.254 | - | - |
| 43 | ATP500 | Inactive | Vlan_Silverfish_Entertainment | 192.168.43.254 | - | - |
| 44 | ATP500 | Active | Vlan44_vbqspeakers | 192.168.44.254 | - | - |
| 45 | ATP500 | Inactive | Vlan45_SnafuPictures | 192.168.45.254 | 157.231.128.137 | inactive, ports still assigned |
| 46 | ATP500 | Active | vlan46_AcmeFireCult | 192.168.46.254 | - | - |
| 47 | ATP500 | - | Vlan47_LatinAmerica | 192.168.47.254 | - | - |
| 48 | ATP500 | Inactive | Vlan48_FieldVision | 192.168.48.254 | - | inactive on sheet but live, inactive, ports still assigned |
| 49 | ATP500 | Active | Vlan49_StudioArchetype | 192.168.49.254 | - | - |
| 50 | ATP500 | Active | Vlan50_AdamAftanas | 192.168.50.254 | - | - |
| 51 | ATP500 | Active | Vlan51_HelenKerridge | 192.168.51.254 | - | - |
| 52 | ATP500 | Active | Vlan52_NordCityltd | 192.168.52.254 | - | - |
| 53 | ATP500 | Active | Vlan53_BridgeTheGap | 192.168.53.254 | - | active on sheet, no hosts |
| 54 | ATP500 | Active | vlan54_Thamesreach | 192.168.54.254 | 157.231.128.136 | - |
| 55 | ATP500 | Active | Vlan55_Studio_Cw208 | 192.168.55.254 | - | - |
| 56 | ATP500 | Active | Vlan56_OpenDemocracy | 192.168.56.254 | - | - |
| 58 | ATP500 | Active | Vlan58_Mediorite | 192.168.58.254 | 157.231.128.138 | - |
| 59 | ATP500 | Active | Vlan59_FullTimeHobbyLtd | 192.168.59.254 | - | no access port found |
| 60 | ATP500 | Active | Vlan60_BalaamMurphyLtd | 192.168.60.254 | - | - |
| 61 | ATP500 | Inactive | Vlan61_ForwardSlashMediaLtd | 192.168.61.254 | - | - |
| 62 | ATP500 | Active | Vlan62_ProjectsOffice | 192.168.62.254 | - | - |
| 63 | ATP500 | Inactive | Vlan63_JoannaRzepczynska | 192.168.63.254 | - | - |
| 64 | ATP500 | Active | Vlan64_TheDustyKnuckleR1 | 192.168.64.254 | - | - |
| 65 | ATP500 | - | Vlan65_TheDustyKnuckleR2 | 192.168.65.254 | - | - |
| 66 | ATP500 | Active | Vlan66_StudioMcDonnell | 192.168.66.254 | - | - |
| 67 | ATP500 | Active | Vlan67_SilverfishProductions | 192.168.67.254 | - | - |
| 68 | ATP500 | Inactive | Vlan68_RapidEyeMovers | 192.168.68.254 | 157.231.128.139 | - |
| 69 | ATP500 | Active | Vlan69_LAWA | 192.168.69.254 | - | - |
| 70 | ATP500 | Active | Vlan70_LeadersUnlocked | 192.168.70.254 | - | sheet public IP is a LAN address |
| 71 | ATP500 | Active | Vlan71_CafeOTO | 192.168.71.254 | 157.231.128.140 | - |
| 72 | ATP500 | Active | Vlan72_AshfordSon | 192.168.72.254 | - | - |
| 73 | ATP500 | Active | Vlan73_MAKE | 192.168.73.254 | - | - |
| 74 | ATP500 | Active | Vlan74_WisemartSolicitors | 192.168.74.254 | - | - |
| 101 | FortiGate | - | vlan101 | 192.168.101.254 | - | not in sheet |
| 102 | FortiGate | - | 102 | 192.168.102.1 | - | not in sheet |
| 150 | FortiGate | Active | CW207 - Create London | 192.168.150.254 | - | - |
| 151 | FortiGate | Active | FH2.1 - ReLine | 192.168.151.254 | 193.221.131.33 (VIP, disabled) | - |
| 152 | FortiGate | Active | PH2.3 - Curamcare | 192.168.152.254 | - | - |
| 153 | FortiGate | Active | PH3.6-8 - Cake Architecture | 192.168.153.254 | - | - |
| 154 | FortiGate | Active | FH2.11 - 01-Profiles Ltd/ Gunga | 192.168.154.254 | - | - |
| 155 | FortiGate | Active | FHG1 - Colab | 192.168.155.254 | - | active on sheet, no hosts |
| 156 | FortiGate | Active | PH3.17-18A - Harp-E | 192.168.156.254 | - | - |
| 157 | FortiGate | Active | PH1.14 - Henry Playfoot | 192.168.157.254 | - | - |
| 158 | FortiGate | Active | Fair Finance | 192.168.158.254 | - | - |
| 159 | FortiGate | Active | St Paul's Waldorf School | 192.168.159.254 | - | - |
| 160 | FortiGate | Active | Simon Campbell | 192.168.160.254 | - | - |
| 161 | FortiGate | Active | Mediorite | 192.168.161.254 | 193.221.131.34 (VIP) | active on sheet, no hosts, no access port found |
| 162 | FortiGate | - | vlan162 | 192.168.162.254 | - | not in sheet |
| 163 | FortiGate | - | vlan163 | 192.168.163.254 | - | not in sheet |
| 164 | FortiGate | - | vlan164 | 192.168.164.254 | - | not in sheet |
| 165 | FortiGate | - | vlan165 | 192.168.165.254 | - | not in sheet |
| 166 | FortiGate | - | vlan166 | 192.168.166.254 | - | not in sheet |
| 167 | FortiGate | - | vlan167 | 192.168.167.254 | - | not in sheet |
| 168 | FortiGate | - | vlan168 | 192.168.168.254 | - | not in sheet |
| 169 | FortiGate | - | vlan169 | 192.168.169.254 | - | not in sheet |
| 170 | FortiGate | - | vlan170 | 192.168.170.254 | - | not in sheet |
| 171 | FortiGate | - | vlan171 | 192.168.171.254 | - | not in sheet |
| 172 | FortiGate | - | vlan172 | 192.168.172.254 | - | not in sheet |
| 173 | FortiGate | - | vlan173 | 192.168.173.254 | - | not in sheet |
| 174 | FortiGate | - | vlan174 | 192.168.174.254 | - | not in sheet |
| 175 | FortiGate | - | vlan175 | 192.168.175.254 | - | not in sheet |
| 200 | FortiGate | - | vlan200-TEST | 192.168.200.254 | - | not in sheet |

Plus FortiGate vlan70 on x1 (alias LeadersUnlocked, 192.168.70.254), the duplicate of ATP500 VLAN 70.
