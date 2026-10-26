---
name: external-ip-fact-finding
description: Tenant external IP fact-finding letters (drafted 14 Oct, sent 15 Oct 2026 by Ryan); who has a dedicated public IP on each gateway; replies and carry-over decisions as of 23 Oct 2026
metadata:
  type: project
---

On 14 Oct 2026 Mat asked for one letter per tenant that has a dedicated public IP or depends on the building's external IP, asking whether they still need it (fact-finding only, no migration plan shared). Reply-by date in the letters: Friday 17 Oct 2026 (Mat shortened it from 28 Oct). Letters cut to three short paragraphs on 14 Oct after Mat said the first drafts were too technical. Letters are Claude Docs titled "External IP check: <tenant>". Signed "The Bootstrap team": Mat hands the letters to the Bootstrap office team to distribute, sender unknown. Mat is not the sender of tenant comms.

Tenant-to-VLAN truth lives in Bootstrap's shared drive, see [[bootstrap-shared-drive]], spreadsheet "2. VLANs and Configurations". Gateway configs alone do not name FortiGate tenants.

ATP500 line (routed block 157.231.128.128/28 behind WAN 157.231.154.206), letters sent: DGN Studio VLAN27 .132 (port forwards still labelled DUPEVFX from Dupe VFX, the previous occupant), Lickerish VLAN31/24 .135, Thamesreach VLAN54 (+39, 12) .136, Snafu Pictures VLAN45 .137 (left PH2.4-5; the sheet said "in CoLab" but the CoLab no longer exists as of 14 Oct 2026, so they may have left entirely; rules orphaned), Mediorite VLAN58 .138 (also has 193.221.131.34 prepared on FortiGate vlan161, not live), Cafe OTO VLAN71 .140.
No letter: Bootstrap VLAN10 .130 (landlord), Tentacle VLAN14 .134 (Mat's own, NO LONGER NEEDED), Curam VLAN11 .131 (moved to FortiGate vlan152, old IP dead), Haberdashery VLAN33 .133 (left), Rapid Eye Movers VLAN68 .139 (left). .141/.142 unused.

FortiGate line (Vorboss 193.221.132.138, secondary 193.221.131.32/27): vlan150 Create London, 151 ReLine (VIP .33 disabled, maps to gateway, no letter), 152 Curam/Curamcare (letter: whitelist rule to *.ecare123.site, shares building IP), 153 Cake Architecture, 154 01-Profiles/Gunga, 155 former Bootstrap CoLab (space no longer exists per Mat 14 Oct 2026; its whitelist rule to "Dupe-FW" 193.221.132.59 is probably dead), 156 Harp-E, 157 Henry Playfoot, 158 Fair Finance, 159 St Paul's Waldorf School, 160 Simon Campbell, 161 Mediorite (VIP .34 active, no hosts yet).

**Why:** the 10G migration (see [[bootstrap-miro-board]]) moves tenants off the ATP500 and changes external IPs; tenants who no longer need a fixed IP can be discounted first.
**How to apply:** when the migration plan is written, check replies against this list. Rules that can go without asking anyone: Tentacle .134, Haberdashery .133/.136, Rapid Eye .139, Curam .131.

Shared-address dependants (added 14 Oct 2026): no tenant has an inbound rule on either shared WAN address (ATP500 157.231.154.206, FortiGate 193.221.132.138); every inbound rule sits on a dedicated IP. The ATP500 secondary WAN 157.125.150.201/29 ("Subnet1") is referenced by nothing. Tenants the register shows were GIVEN the shared address (so an outside system probably whitelists it) got letters too: Cake Architecture (vlan153, .132.138), Reline London (vlan151, .132.138), Abisoye Odugbesan (ATP500 vlan70, .154.206), plus Curam. Total letters in play: 10.

## Replies and decisions (23 Oct 2026, from the Gmail threads, updated by Claude Desktop with Mat's OK)

Letters went out from Ryan on 15 Oct 2026 with Mat cc'd; Ryan dropped Snafu (no longer a tenant) and AO Studio/Abisoye (no longer in the building). Tentacle: Mat told Shopna it is separate and no longer needs a public IP.

Addresses decided by Mat 23 Oct 2026: Thames Reach 193.221.131.35, Cafe OTO 193.221.131.36, Mediorite 193.221.131.34 (unchanged). Every other tenant shares the FortiGate WAN address 193.221.132.138 after the move, the same one the FortiGate tenants use today (so Curam's ecare123 allow-list and anyone who whitelisted Cake or Reline are untouched). Lickerish, if someone whitelists them: 193.221.132.138. Letters quoting them, with the cutover date Tue 27 Oct 2026: notes/tenant-comms-2026-10-27/.

Carry over to the FortiGate (three new public IPs from 193.221.131.32/27, .34 already Mediorite's):
- Thames Reach (Akos Kovacs): YES, keep everything as is. Wants notice and will liaise with their IT provider, a few days' lead time. ATP500 has .136 SNAT plus 1:1 NAT any -> 192.168.54.253. Build VIP 1:1 to their firewall plus matching outbound SNAT; confirm which box is 192.168.54.253. The deactivated VLAN33_Haberdashery rule on .136 stays behind.
- Cafe OTO (James Dunn, their IT): YES. Says BlackBox set up "CGNAT" with ports 1000 to 2000 to their internal IP. The ATP500 rule as captured is muddled (virtual server .140 -> 192.168.71.254, the ATP500's own VLAN71 address, then a vlan71 rule remapping to the router 192.168.71.1; typo object 192.186.71.1; unused service objects 1000-5000 and 1800-1900). Do not copy it: build a fresh VIP to 192.168.71.1 (1:1 or TCP+UDP 1000-2000) plus outbound SNAT. Confirm the router WAN address with James.
- Mediorite (Anthony): YES, critical, NinjaOne Remote for editors at home. Wants the IP ported, asks what is physical and timescales; has router config that "doesn't work as things stand" (probably the vlan161 details given before the port was moved). ATP500 has .138 with TCP 1-5000 and UDP 1-5000 -> 192.168.58.3. FortiGate vlan161 with VIP 193.221.131.34 -> 192.168.161.250 (already 1:1, port forwarding disabled) and the inbound policy exist; no hosts, no DHCP server on vlan161, and VLAN 161 is tagged (not PVID) on SW03 p7, Mediorite's VLAN 58 port. Under plan v2 (notes/migration-plan-v2-2026-10-23.md) 161 becomes VLAN 86, so: change SW03 p7 PVID to the new VLAN, put the device on the VIP's mapped address or repoint the VIP, add a DHCP scope, check outbound SNAT uses .34. Reply to Anthony: new IP 193.221.131.34, no new cabling, port swap on a date. (Corrected 23 Oct 2026 by Claude Code from the 13 Oct FortiGate config.)

Not carried over:
- DGN Studio (Geraldine): NO, don't need it. .132 and the DUPEVFX forwards die with the ATP500.
- Curam (Hector, Patrick): unsure, then "all good, understood" after Mat said if unsure they don't need it. Already on vlan152 behind the shared Vorboss IP, which does not change, so the ecare123 whitelist is unaffected. Wants notice of works.
- Lickerish (Emma): doesn't know what it is, "if it relates to FTP services we use then yes", no IT support. Device: VLAN24 is their live network (1 lease, SW04 p5), no public IP; the .135 1:1 NAT (FTP, FTPS, HTTP, HTTPS inbound to 192.168.31.253) sits on VLAN31, which has no leases, no ARP and no access port, and there is no outbound SNAT on .135. Treat as orphaned: move VLAN24 as a plain tenant, do not carry .135 or VLAN31. Open question for Emma: do people connect in to an FTP server in the office, or do they connect out to clients' FTP? If someone whitelists them, give them the new shared address after the move.
- Cake Architecture (Sarah) and Reline London (Freya): no reply as of 23 Oct. Both already on the FortiGate behind the shared IP, nothing moves. Reline's disabled VIP .33 can be deleted at lockdown.

Everyone who answered yes, plus Curam, asked for notice of the work.

Source note (Claude Code, 23 Oct 2026): the replies above were read from the Gmail threads by Claude Desktop; Claude Code could not re-read them. Mat confirmed the same day that Thames Reach, Cafe OTO and Mediorite carry a public IP to the FortiGate, with two new addresses from 193.221.131.32/27 for the first two and .34 staying Mediorite's. The ATP500 rule details in this section match the 13 Oct running-config.
