---
name: bootstrap-records
description: "Bootstrap's own VLAN workbook ingested 14 Oct 2026 into /srv/configs/bootstrap-records with a cross-reference against device captures; how Mat wants it treated and the headline gaps"
metadata:
  node_type: memory
  type: project
  originSessionId: a30ac655-8b7f-4cba-8fda-278d8b49bcd1
  modified: 2026-10-14T16:57:01.930Z
---

Bootstrap's "2. VLANs and Configurations" workbook (shared drive 0AO-R8iXcHrdqUk9PVA, file 1B7f9t3k-GedYiUYD-l51Kq8HGOty4n2w, last edited 7 Oct 2026) and the Dec 2025 copy "VLANS_NAT 01.12.25.xlsx" from Mat's A254_BStrap folder are in /srv/configs/bootstrap-records/ (xlsx + CSV per tab, NOTES.md, crossref-2026-10-14/, tools/crossref.py). Mat's summary: ~/jumpbox-setup/BOOTSTRAP-SHEET-CROSSREF-2026-10-14.txt.

Mat's framing (14 Oct 2026): the workbook is *Bootstrap's* source of truth, not ours. Consume it, check it against reality, and treat its margin notes as the best evidence of what Bootstrap intends for the migration. Do not adopt it as target state.

Headline gaps found: VLAN 70 is defined on both gateways with the same subnet; VLAN 48 is "reusable" on the sheet but live (21 leases); dead SNAT/NAT for VLANs 11, 33, 45, 68 still on the ATP500; VLAN 72 has no bandwidth rule (bwm 4 misapplied to vlan73); FortiGate VLANs 162–175 are a pre-built spare pool not in the sheet; VLAN 161 Mediorite contradicts itself; VLANs 59/67/40 ride undefined-VLAN tag forwarding through SW02. 18 stale port rows listed in the report.

Not retrievable via the Drive connector: the two shortcuts ("ORDERS TO ACTION" form responses, "Configuration Record") and the Network Diagrams / Troubleshooting References folders. Mat to check in a browser.

**How to apply:** for tenant names, rooms and intent use bootstrap-records; for what is configured use the device captures. Re-run tools/crossref.py after any new capture. Related: [[bootstrap-jumpbox]], [[switch-layer]], [[external-ip-fact-finding]], [[mat-operator]].
