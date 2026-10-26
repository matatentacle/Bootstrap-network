---
name: migration-plan-v2
description: Gateway migration plan v2 (23 Oct 2026). FortiGate x1+x2 20G LAG to SW101, every tenant VLAN 10 to 99 on it, FortiGate tenants renumbered from 150-160 to 75-85, mgmt moved to 192.168.5.0/24 first, ATP500 tenants cut over cabinet by cabinet.
metadata:
  type: project
---

# Bootstrap gateway migration, plan v2 (23 Oct 2026)

Drafted 2026-10-23 by Claude Desktop from a planning session with Mat. Checked against the
13/14 Oct captures and corrected by Claude Code the same day; Mat confirmed the physical
design, the order and the management move in writing on 23 Oct 2026. Supersedes the 14 Oct
plan (FACTS.md "Migration", notes/bootstrap-miro-board.md) on cutover method. The Miro "10G
migration plan" frame still holds the physical layout and the shopping list.

Decided by Mat 23 Oct 2026: physical design, order, mgmt subnet, cabinet-by-cabinet cutover
and cabinet order, SW102 port 12 to SW01 port 24 for the inter-island trunk during the
migration, PlanetB on VLAN 87, every VLAN 10 to 99 created with a client name only where a
tenant is active, ReLine's VIP .33 deleted at lockdown, generated CLI kept in a committed
`plans/` directory, aggregate named LAN-Bond-10G (section 11). Permanent SW01 uplink is SW102
SFP 6 to SW01 port 25 once PH3 has moved. PlanetB are already on the FortiGate: vlan70 on x1
via SW101 port 1 to SW14 in FHG, so clearing x1 means a short planned outage for them and for
island management, which Mat has accepted (section 7). The only thing left to read off Nebula is
which SW14 ports PlanetB are on (section 11).

Everything below that changes state on a gateway or switch is Mat's to do or to watch being
done. Read-only checks (section 10) can be run through bin/jb without asking.

## 1. The idea in one paragraph

Build a new 20G aggregate on FortiGate x1+x2 into SW101 and put every tenant VLAN the site will
ever have on it (IDs 10 to 99). The live ATP500 VLANs are replicated with their existing IDs and
subnets. The existing FortiGate tenants (150 to 161, children of LAN-Bond-2 on port3+port4)
cannot be moved to a new parent in FortiOS, so they are renumbered into 75 to 86 on the new
aggregate instead. The ATP500 tenants then move to the FortiGate replicas cabinet by cabinet:
every cabinet trunk carries VLANs 10 to 99, and re-patching a cabinet from SW01/SW02 to
SW101/SW102 is the gateway cutover for everything in it (section 4). The new fibre runs are
patched next to the existing ones so each swap is a single re-patch.

## 2. Physical backbone (Mat, 23 Oct 2026)

- FortiGate x1 + x2 (10G SFP+) LACP to SW101 SFP 1 + 2: a 20G LAG, both members on SW101.
  Mainly for redundancy; there is no inter-VLAN routing, so one 10G link carries the load.
  Today SW101 port 1 holds the singlemode run to SW14 (FHG ground floor, 192.168.201.4); that
  run moves to SW101 SFP 3 to free ports 1+2. x1 is on SW101 port 10 today and moves to port 1;
  x2 goes to port 2 (Mat, 23 Oct).
- SW101 to SW102: 10G LAG on the two RJ45 ports 11 and 12 of each switch, for backbone
  redundancy. During the migration only port 11 links the two switches, because SW102 port 12
  is lent to the SW01 trunk; the LAG on 11+12 is activated once every cabinet has moved and the
  SW01 trunk is no longer needed.
- Fibre from SW101 and SW102 to the floor patch panels, new fibre patched into the port next
  to the existing one so each cabinet can be swung with minimal downtime. Load split across
  the two switches:

| Island port | Panel | Cabinet / panel port |
|---|---|---|
| SW101 SFP 3 | P1 | FHG port 2 (the existing singlemode run to SW14, moved from SW101 port 1; no new fibre) |
| SW101 SFP 4 | P2 | PH3 port 2 |
| SW101 SFP 5 | P2 | PH2 port 10 |
| SW101 SFP 6 | P2 | PH1 port 18 |
| SW102 SFP 1 | P3 | Basement port 2 |
| SW102 SFP 2 | P3 | FH3 port 10 |
| SW102 SFP 3 | P3 | FH2 port 18 |
| SW102 SFP 4 | P4 | CW3 port 2 |
| SW102 SFP 5 | P4 | CW2 port 10 |
| SW102 port 12 (RJ45) | - | SW01 port 24, Cat6: interim inter-island trunk during the migration |
| SW102 SFP 6 | - | SW01 port 25, 1G SX fibre: permanent SW01 uplink once PH3 has left port 25 |

- SW01 is not retired. It stays as the main comms room switch serving its own floor, uplinked
  to the island. SW02 retires (Mat, 23 Oct 2026).
- Interim trunk during the migration: SW102 copper port 12 to SW01 copper port 24 over Cat6.
  SW01 port 24 was down with no LLDP neighbour on 14 Oct, so it is free. No optic needed.
- Permanent uplink: SW102 SFP 6 to SW01 port 25 over fibre (1G SX in SW102, SW01 reuses the
  module already in port 25), as the Miro plan has it. Port 25 is PH3 SW12's uplink today and
  becomes free when PH3 is re-patched to SW101 SFP 4. After the nine cabinets are done: patch
  SFP 6 to port 25, pull the port 24 copper, and SW102 port 12 rejoins the SW101 LAG.
- Today: ATP500 ge4 1G to SW01 port 2 carries VLANs 10 to 74; FortiGate LAN-Bond-2 (port3+port4)
  to SW01 ports 9+10 (trunk T1) carries 150 to 175. x1 (192.168.201.1/24) goes to the island and
  carries vlan70 and vlan200-TEST; x2 and x3 are members of the fortilink aggregate.

## 3. Agreed order (Mat, 23 Oct 2026)

0. Move FortiGate management off 192.168.10.0/24 (section 6). Must come first: the VLAN 10
   replica cannot be created while mgmt overlaps it.
1. Build the x1+x2 LAG, all VLANs 10 to 99 on it, SW101/SW102 trunks. Test with a port on SW101.
2. Tidy the Nebula VLAN tables; bring up the SW102 to SW01 trunk carrying 75 to 99 only.
3. Renumber the FortiGate tenants to 75 to 85 at leisure. Delete 150 to 175 from LAN-Bond-2
   when done.
4. Re-patch cabinets to SW101/SW102 one at a time; each re-patch moves that cabinet's tenants
   from the ATP500 to the FortiGate replicas (section 4). Retire SW02 when its cabinets are gone.
5. (merged into 4)
6. Power off the ATP500; delete LAN-Bond-2 and free port3/port4.

## 4. Step 4: cabinet by cabinet (decided by Mat, 23 Oct 2026)

Once the FortiGate tenants are renumbered (step 3), the cutover unit is the cabinet. Every
trunk port from SW101/SW102 to a cabinet carries VLANs 10 to 99. Re-patching a cabinet switch
from its SW01/SW02 uplink to its SW101/SW102 port puts everything in that cabinet on the
FortiGate replicas in one go. The SW102 to SW01 trunk stays at 75 to 99 for its whole life, so
VLANs 10 to 74 never have a path between the two islands and the ATP500 never sees a replica.

Per cabinet:
1. Confirm the FortiGate replicas for that cabinet's VLANs are up and the cabinet's new fibre
   is patched into the SW101/SW102 port with 10 to 99 allowed.
2. Unplug the cabinet's old uplink from SW01/SW02 first, then bring the new one up. Both live at
   once bridges the two islands on every VLAN; a tagged frame leaking the other way is the
   failure to avoid, so this is one move at a time, not add-then-remove.
3. Clients re-ARP or renew. Check a host in each tenant, move on.
Rollback is the same re-patch reversed.

Cabinet order (Mat, 23 Oct 2026), following the patch map: FHG (SW101 SFP 3), PH3 (SFP 4),
PH2 (SFP 5), PH1 (SFP 6), Basement (SW102 SFP 1), FH3 (SFP 2), FH2 (SFP 3), CW3 (SFP 4),
CW2 (SFP 5). The main comms room is not a re-patch: SW01 stays and keeps serving its own floor,
reached through the SW102 to SW01 trunk (copper port 24 during the migration, fibre to port 25
after PH3 has moved). Its tenants cut over when SW01 port 2 (the ATP500 uplink) is unplugged,
which is the last swap before step 6. SW02 retires once its cabinets have moved.

Split VLANs: a VLAN with ports in more than one cabinet runs on two gateways with the same
subnet until all its cabinets are over; hosts in the two halves cannot see each other
meanwhile. Mat accepts this for VLAN 10 (Bootstrap's own, on SW01, SW02, SW05, SW12 and SW13):
it goes when it goes, no special ordering. Read-only check 1 lists any other VLAN in the same
position so Mat knows before each swap. Thames Reach's 54/39/12 are all on SW08, fine.

The alternative that was considered, moving one VLAN at a time through the SW102 to SW01
trunk allowed-list, is not being used; it would have put ATP500 VLANs on that trunk.

## 5. VLAN plan

Convention throughout: VLAN N = 192.168.N.0/24, gateway .254, name carried over.

| Today | New | Note |
|---|---|---|
| ATP500 10 to 74 | same IDs, same subnets | replicate on the new LAG; VLAN 10 needs the mgmt move first |
| FortiGate 150 to 160 | 75 to 85 (150 to 75, 151 to 76 ... 160 to 85) | eleven configured VLANs, ten with hosts on 14 Oct; 155 CoLab becomes 80, created like the rest but with no client name since CoLab is gone |
| FortiGate 161 Mediorite | 86 | no hosts yet; VIP 193.221.131.34 remapped to a host in 192.168.86.0/24 |
| PlanetB (today on FortiGate vlan70 via x1, SW101 port 1, SW14 in FHG) | 87 | next available number (Mat, 23 Oct); client name on the interface. The FortiGate's vlan70 (alias LeadersUnlocked) actually serves PlanetB, not Leaders Unlocked |
| FortiGate 162 to 175 spares | 88 to 99 | twelve spares, no client name |
| 57 | created, no client name | the only unused ID in 10 to 74 on the ATP500; not in the workbook |
| FortiGate vlan70 on x1 | deleted once PlanetB are on 87 | its only users are PlanetB via SW14; the alias "LeadersUnlocked" is stale config (Mat, 23 Oct). Leaders Unlocked (ATP500 VLAN 70) is served by the replica like any other tenant |
| FortiGate vlan200-TEST, vlan101, 102 | deleted | relics of old config, nothing uses them (Mat, 23 Oct) |
| FortiGate fortilink aggregate (x2+x3, 10.255.1.1/24) | deleted | no managed FortiSwitches in the 13/14 Oct captures; frees x2 for the new LAG and x3 as a spare (Mat, 23 Oct) |
| 100 | never used | the `lan` hard-switch owns 192.168.100.0/24 |

Nothing above 100 survives apart from the infrastructure subnets: 192.168.5.0/24 (new mgmt),
192.168.201.0/24 (island management), 192.168.254.0/24 (ATP500 mgmt until it is switched off).

## 6. FortiGate management re-address (step 0)

Problem: FortiGate `mgmt` is 192.168.10.99/24 and ATP500 VLAN 10 (Bootstrap's own) is
192.168.10.0/24. FortiOS refuses an overlapping subnet on a second interface, so vlan10 cannot
be created on the new LAG until mgmt moves. Mat's decision (23 Oct 2026): move mgmt to
192.168.5.0/24, not VLAN 10. Suggest keeping .99 for the FortiGate and .98 for the jump box.

Lockout risk: mgmt is the only interface we can reach the FortiGate on (x4 HTTPS is a lockdown
item, not a working path for us). Nothing is removed until the new address is proven.

Touches: FortiGate `mgmt`; jump box onboard NIC (enp3s0, 192.168.10.98/24 static); Tailscale
advertised route 192.168.10.0/24 on MINI-PC-6; tailnet ACL if it names that subnet;
`private/jb.env` and the expect scripts in `jumpbox-setup/` that hold the FortiGate address;
`jumpbox-setup/README.md`; FACTS.md.

Sequence (Mat at the keyboard, with console lead to hand):
1. FortiGate: add 192.168.5.99/24 as a secondary IP on `mgmt` (`set secondary-IP enable`,
   `config secondaryip`, allowaccess ping https ssh). The old address keeps working.
2. Jump box: add 192.168.5.98/24 to enp3s0 (netplan) alongside the old address. Test SSH to
   192.168.5.99 through bin/jb with a temporary override.
3. Advertise 192.168.5.0/24 from Tailscale alongside the old route; approve it in the admin
   console; test from Mat's laptop.
4. Swap: make .5.99 primary on `mgmt`, drop the old secondary; drop the old address and route
   on the jump box; update jb.env, scripts, README, FACTS.
5. Only then create vlan10 on the new LAG.

Rule reminder: the USB NIC and Tailscale on the box are not touched without Mat watching. This
touches the onboard NIC and Tailscale routes, so it is a Mat-present job.

## 7. FortiGate build (step 1)

Clear x1 and x2 first. Both are FortiOS requirements, not tidiness:
- x2 is a member of the `fortilink` aggregate (with x3). Mat's decision (23 Oct 2026): the
  aggregate goes entirely. The 13/14 Oct captures show no managed FortiSwitches, so nothing
  depends on it. Delete its DHCP server, `set fortilink disable` on the interface, then delete
  the aggregate. x2 and x3 are both free afterwards; x3 stays spare. `switch-controller enable`
  in system global can stay or be disabled, either is harmless.
- x1 has 192.168.201.1/24 and is parent of vlan70 and vlan200-TEST. An interface with an
  address or child VLANs cannot join an aggregate. Delete in dependency order: policies 32
  (vlan70), 33 (vlan200-TEST) and 34 ("Interface LAN x1"); the address objects "vlan70
  address", "vlan200-TEST address", "x1 address"; the DHCP servers on vlan70, vlan200-TEST and
  x1; the two VLAN interfaces; then `unset ip` on x1. FortiOS says "entry is used" if anything
  is missed, which is a safe failure.

PlanetB ride x1 today (vlan70, via SW101 port 1 to SW14 in FHG), and so does the island's
management subnet 192.168.201.0/24. Clearing x1 therefore drops PlanetB and Nebula's view of
SW101/SW102/SW14 until LAN-Bond-10G is up with the same 192.168.201.1/24 and VLAN 87 reaches
SW14. The clean way is a short planned window with Mat at the console: clear x1, build the
aggregate with x1+x2, bring up 192.168.201.1/24 and VLAN 87 on it, re-patch SW101 ports 1+2,
move SW14's PlanetB ports from PVID 70 to 87 in Nebula. Minutes, not hours, but PlanetB should
be told. Staging via x2 alone first would avoid the gap but needs a temporary second
management subnet on the island, which is more risk than it saves. Mat accepted the window on
23 Oct 2026.

SW14 (FHG Ground Floor, GS1920-24HP, bc:cf:4f:bb:c4:6c) gets its management address
192.168.201.4 by DHCP from 192.168.201.1, on untagged VLAN 1, gateway 192.168.201.1, DNS 8.8.8.8
(Nebula, 23 Oct). That DHCP server lives on x1 today, so it must be recreated on LAN-Bond-10G
with the same range before x1 is cleared, or SW14 loses its address when the lease expires.
Check whether SW101 and SW102 (.2 and .3) are DHCP or static at the same time.

New aggregate LAN-Bond-10G (Mat, 23 Oct): type aggregate, member x1 x2, lacp-mode active,
IP 192.168.201.1/24 untagged, allowaccess ping. The untagged side carries the island
management (SW101 .2, SW102 .3, SW14 .4) exactly as x1 does today, so nothing changes on
those switches. The x1 DHCP server (192.168.201.0/24) is recreated on the aggregate: SW14 gets
its address from it.

Tenant VLAN interfaces 10 to 99 as children of the aggregate, generated from the captures:
- ATP500 replicas: interface and DHCP server (range, lease time, DNS, static bindings) from
  `configs/atp500/running-config-2026-10-13.conf`; the ATP500 is the source for these scopes.
- Renumbered FortiGate tenants: copy the existing vlan15x interface and DHCP server, changing
  only ID, name and third octet. The 13 Oct config has no DHCP reservations anywhere, so there
  is nothing to carry; vlan161 has no DHCP server at all today.
- PlanetB on 87: interface, DHCP and policy like any active tenant. Copy the scope shape from
  the FortiGate's vlan70 (their current DHCP server), changing the third octet.
- 57 and spares 88 to 99: interface and DHCP only, no policy, mirroring the 162 to 175 pattern.

Naming rule (Mat, 23 Oct 2026): every VLAN 10 to 99 is created, active or not. An interface
whose VLAN has an active tenant carries that client's name (FortiOS `alias`, 25 characters, and
`description` for the long form). An inactive or spare VLAN carries no name at all; the ATP500's
old descriptions for inactive VLANs (Curam, bars, Pango, Snafu and so on) are not copied. The
workbook status plus the 14 Oct leases decide active; the list goes to Mat with the CLI block.

Public addressing (Mat, 23 Oct): the new interface and the ATP500 arrivals get new shared
addresses from 193.221.131.32/27 as an overload IP pool, so the existing FortiGate tenants
keep egress on 193.221.132.138 and nothing on the live side changes. No IP pools exist on the
FortiGate today. Policies: one accept + NAT per VLAN to x4, mirroring the existing pattern.
Dedicated fixed-port pools on their own policies for Thames Reach (VLAN 54) and Cafe OTO
(VLAN 71), two addresses from the /27 to be chosen (.34 is Mediorite). Mediorite's VIP .34 is
already 1:1 (portforward disabled), so only its mapped address changes, to the host in
192.168.86.0/24. ReLine's disabled VIP .33 and its policy 5 are deleted at lockdown and .33
returns to the pool (Mat, 23 Oct). Build notes per tenant: notes/external-ip-fact-finding.md.

Generate the whole thing as one reviewable CLI block, saved in a new committed `plans/`
directory (Mat, 23 Oct; it holds only interface, DHCP and policy definitions derived from the
committed captures, and the pre-commit hook scans it), never pasted into chat. Mat applies it
from the console or via bin/jb shell with the write allowlist deliberately not relaxed.

Test before step 2: an access port on SW101 in a replicated VLAN gets a lease from the
FortiGate, reaches the internet via the new pool address, and cannot see the ATP500 copy of
the same VLAN (there is no path yet, so this is a sanity check of isolation).

## 8. Switch side (steps 1 to 4)

SW101 (XS1935-12F, Nebula): two-port LACP trunk on SFP 1+2 to the FortiGate carrying 10 to 99
tagged, management untagged on VLAN 1 (as x1's port 10 does now). x1 moves from port 10 to
port 1, x2 lands on port 2, FHG's singlemode run moves from port 1 to SFP 3. SW101 to SW102
LAG on ports 11+12, all VLANs.

Nebula VLAN tables before the SW102 to SW01 trunk goes live. The GS1920s forward tagged frames
for VLANs not in their VLAN table (VLANs 40, 59 and 67 depend on this today). With the trunk up,
any undefined VLAN leaks straight across and puts both gateways in one broadcast domain. So:
every VLAN 10 to 99 defined on SW01, SW102, SW101 and every cabinet switch, with the
inter-island trunk ports excluded by default; fix 40, 59, 67 properly; then prove with one spare
VLAN that exclusion really blocks it before any live tenant depends on it.

Inter-island trunk SW102 to SW01 (port per section 2): allowed list is 75 to 99 only, and
VLANs 10 to 74 are never added to it. Cabinet trunk ports on SW101/SW102 carry 10 to 99.

Renumbering (step 3): for each FortiGate tenant, change the PVID on its access ports and the
VLAN tag on its SSIDs from 15x to 7x/8x in Nebula; clients renew and land on the new subnet via
the SW01/SW102 trunk, SW101, the new LAG. Those tenants ride the single 1G inter-island trunk
until their cabinet is re-patched, no worse than the 1G bond they use now. Delete the vlan15x
interface from LAN-Bond-2 only after the tenant is confirmed on the new ID. Ports today, from
port-check.txt: 150 SW05 p8; 151 SW06 p3; 152 SW04 p12; 153 SW12 p3-p6 (and SW13 p4 tagged);
154 SW06 p1; 155 SW07 p12; 156 SW13 p4; 157 SW03 p16; 158 SW06 p10, p12; 159 SW04 p8, p10;
160 SW03 p6; 161 tagged on SW03 p7 (Mediorite's VLAN 58 port). SSID to VLAN mapping is not in
the captures; Mat to read it off Nebula.

## 9. Other tricky bits

- DHCP lease overlap: the FortiGate does not know the ATP500's leases. Shorten ATP500 lease
  times on the tenant VLANs about a week before step 4 so stale leases expire quickly after
  cutover. FortiOS DHCP checks for an address in use before offering, which covers the rest.
- Hardware: everything on `jumpbox-setup/SHOPPING-LIST-10G-2026-10-14.txt` has been bought and
  is on site (Mat, 23 Oct 2026). The 14 Oct list still matches the plan: the SX module and fibre
  lead for SW102 SFP 6 serve the permanent SW01 port 25 uplink, the interim copper link is a Cat6
  lead from stock, and FHG needs nothing because its singlemode run just moves from SW101 port 1
  to SFP 3. The list carries a 23 Oct amendment recording this.
- Public IP letters: Thames Reach and Cafe OTO need their new address and a date (Thames
  Reach's IT provider wants a few days). Mediorite's .34 is unchanged. See
  notes/external-ip-fact-finding.md.
- Dead ATP500 public-IP plumbing (Tentacle .134, Haberdashery .133/.136 rule, Rapid Eye .139,
  Curam .131) is not replicated. Lickerish's .135 and VLAN 31 are not replicated either.
- Management of the ATP500 (192.168.254.0/24 via the jump box USB NIC) is untouched until step 6.
- LAN-Bond-2 and the SW01 ports 9+10 LAG stay exactly as they are until step 6.
- The Miro "10G migration plan" frame is the source for physical layout. Mat to add a
  "New Plan v2, 23 Oct" sticky so the board and the repo agree; until then this note wins on
  cutover method and the board wins on physical layout.

## 10. Read-only checks to run first (bin/jb, no permission needed)

1. Which VLANs have ports in more than one cabinet (for section 4), from vlan-register.txt and
   the switch configs.
2. ATP500 DHCP scopes, lease times and static bindings per VLAN, for the replica generation.
3. Host counts per FortiGate tenant VLAN from a fresh ARP capture (14 Oct: hosts on 150 to 154
   and 156 to 160; none on 155 and 161).
4. Whether 40, 59, 67 are in SW01's and SW102's VLAN tables, and which other VLANs are missing.
5. SW01 port 2 and ports 9+10 current VLAN membership (14 Oct: port 2 is fixed in every static
   VLAN including 150 to 175).
6. Aggregate state on the FortiGate. `diagnose netlink aggregate name LAN-Bond-2` returned
   "Unknown action 0" for the read-only account on 14 Oct; try `diagnose netlink aggregate list`
   or run it from Mat's account. Confirm the 120G accepts x1/x2 in a new aggregate.
7. (done: x1 is on SW101 port 10, Mat 23 Oct.)
8. PlanetB's ports on SW14 (FHG, 192.168.201.4) and their PVID. SW14 is not reachable from the
   jump box; Mat reads it off Nebula, or Claude Code does once the Nebula API access Mat is
   negotiating comes through. The FortiGate ARP table for vlan70 shows their hosts.
9. Whether SW101 and SW102 take 192.168.201.2/.3 by DHCP from x1 or hold them statically.

## 11. Decisions

Decided by Mat, 23 Oct 2026:
- New mgmt subnet 192.168.5.0/24 (.99 FortiGate and .98 jump box suggested, not yet confirmed).
- Inter-island trunk: SW102 copper port 12 to SW01 copper port 24 during the migration; then
  SW102 SFP 6 to SW01 port 25 over fibre once PH3 has left port 25, the copper comes out, and the
  SW101 to SW102 LAG on ports 11+12 is activated. SW01 stays as the main comms room switch.
- FHG's singlemode run moves from SW101 port 1 to SFP 3; x1+x2 take SW101 ports 1+2.
- PlanetB (today on FortiGate vlan70 via SW14) move to VLAN 87; vlan70 on x1 goes after that.
- Cutover cabinet by cabinet in patch-map order (section 4); VLAN 10 goes when it goes.
- PlanetB gets VLAN 87, the next available number.
- ReLine's VIP 193.221.131.33 and policy 5: delete at lockdown, .33 back to the pool.
- Generated CLI lives in a new committed `plans/` directory.
- The new aggregate is named LAN-Bond-10G.
- Every VLAN 10 to 99 is created. Active tenant: client name on the interface. Inactive or
  spare: no name. So 80 (ex-CoLab) and 57 exist, unnamed, and the inactive ATP500 VLANs (11, 12,
  19, 22, 23, 25, 29, 30, 43, 45, 48, 61, 63, 68 and the unlisted 31, 47, 65) are recreated
  without their old descriptions. 48 counts as active (21 leases on 14 Oct) despite the sheet.

Background on the last three, for the record: ReLine's VIP was a disabled 1:1 NAT from .33 to
192.168.151.254, the FortiGate's own gateway address on ReLine's VLAN, with a disabled
ping-only policy behind it, so it never did anything and ReLine did not answer the letter. The
CLI block is the FortiGate configuration for the aggregate, the 90 VLAN interfaces, their DHCP
scopes and policies, written by Claude Code for Mat to read and paste. The aggregate name is
the FortiOS interface name (15 characters max) beside the existing LAN-Bond-2.

Also confirmed by Mat, 23 Oct 2026: the short outage for PlanetB and island management while
x1 is cleared is acceptable; vlan200-TEST and VLAN 200 are relics with no users; x1 is on
SW101 port 10 today. Still to read off Nebula: PlanetB's ports on SW14 (check 8).

## 12. Repo updates as the plan lands

- FACTS.md: mgmt address and jump box lines after step 0; VLAN table as tenants renumber;
  "Updated" line each time.
- notes/bootstrap-miro-board.md: point at the v2 sticky once it exists.
- jumpbox-setup/README.md and private/jb.env: new mgmt address.
- configs/fortigate/NOTES.md: new aggregate, x1/x2 state, renumbered VLANs after each capture.
