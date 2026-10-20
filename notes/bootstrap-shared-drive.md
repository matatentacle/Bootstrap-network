---
name: bootstrap-shared-drive
description: Bootstrap's working spreadsheets live in a Google shared drive Mat has access to; the VLAN and tenant register is "2. VLANs and Configurations"
metadata:
  type: reference
---

Bootstrap's shared Google Drive: https://drive.google.com/drive/folders/0AO-R8iXcHrdqUk9PVA (shared drive id 0AO-R8iXcHrdqUk9PVA). Readable through the Google Drive connector in this session.

Contents (14 Oct 2026): "2. VLANs and Configurations" (xlsx, file id 1B7f9t3k-GedYiUYD-l51Kq8HGOty4n2w, last edited 7 Oct 2026) is the tenant register: tenant name, building, room, switch and port, VLAN, public IP notes, plus tabs mirroring the ATP500 policy routes, NAT and SNAT tables and the FortiGate VLAN list 150 to 161. Also "Bootstrap Broadband Order form" (Google Form), a shortcut "1. ORDERS TO ACTION: Broadband Tenant Orders (Form Responses)", and folders Network Diagrams, Archive, Troubleshooting References.

**How to apply:** use the register to name tenants per VLAN; the gateway configs name ATP500 VLANs but not FortiGate ones. Treat the sheet as Bootstrap's record, it can lag the live config (for example it still shows VLAN 161 as both "FF, not needed" and "Mediorite").
