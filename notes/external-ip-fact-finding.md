---
name: external-ip-fact-finding
description: Tenant external IP fact-finding letters drafted 14 Oct 2026; who has a dedicated public IP on each gateway, reply deadline 28 Oct 2026
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
