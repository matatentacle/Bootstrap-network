---
name: cutover-runbook-2026-10-27
description: Mat's step-by-step for the gateway cutover, Tuesday 27 Oct 2026 (plan v2); which plans/2026-10-27 file to paste when, Nebula work, cabinet order, checks, rollback
metadata:
  type: project
---

# Gateway cutover, Tuesday 27 October 2026: the day doc

Written 23 Oct 2026 by Claude Code for Mat. Follows notes/migration-plan-v2-2026-10-23.md
(Mat's decisions, 23 Oct). The CLI is generated, not hand-typed: `plans/2026-10-27/*.txt`
from `plans/gen-fortigate-cli.py` (re-run after any capture or decision change). Read
`plans/2026-10-27/summary.txt` first; it is the one-page review of what every VLAN becomes.

Every paste below changes a production gateway or switch. Mat at the keyboard for all of it.

## 0. Before Monday: four decisions, three replies

Decided 23 Oct 2026 and quoted in the letters, so no longer open: one shared public address for
everyone, the FortiGate's own 193.221.132.138 (plain NAT, no pool), which the live FortiGate tenants
already use and some have allow-listed. Only tenants who asked get their own, from 193.221.131.32/27:
.35 Thames Reach, .36 Cafe OTO, .34 Mediorite (unchanged). .33 is freed from ReLine at lockdown;
.37 to .62 stay spare.

Decisions still open (edit the top of `plans/gen-fortigate-cli.py`, re-run, re-read summary.txt):

1. Mediorite: the generator keeps them on VLAN 58 and repoints VIP .34 to 192.168.58.3
   (`MEDIORITE_ON_58 = True`). Plan v2 said VLAN 86 (ex-161). Staying on 58 means nothing changes
   inside Mediorite, which is what their letter promises. VLAN 86 is then an unnamed spare. If you
   want 86 after all, flip the flag, re-run, and reword their letter (their internal addresses change).
2. VLAN 13 cap: generator carries the ATP500's 40000/10000 kbps. If the therapy block raise is
   approved, change it in summary terms to 61440/61440 before pasting (one line in 40-fgt-build).
3. VLAN 72/73: ATP500 has both rules on vlan73. Generator puts 100M on 72 (Ashford) and 30M on 73
   (MAKE / Civil Society). Say if that is wrong.
4. Web filtering: every new policy copies the FortiGate's existing pattern (webfilter "default",
   dnsfilter "default", application control "default"). The ATP500 tenants have not had this.
   Expect the odd "site blocked" call after cutover; the fix is the webfilter profile, not the plan.

Replies needed by Monday 26 Oct: Thames Reach (Akos), Cafe OTO (James), Mediorite (Anthony) saying
Tuesday is fine. Letters: `notes/tenant-comms-2026-10-27/`. If Thames Reach say no, their cabinet
(CW3, SW08) is simply done on their day; everything else goes ahead. Cafe OTO sit on SW02 port 7
in the main comms room, so they move at the very last step (section 5), tell James "late afternoon".

Still to read off Nebula before Tuesday: PlanetB's ports on SW14 (plan check 8); whether SW01 and
the cabinet switches hold their 192.168.1.x by DHCP (Switch > IP settings; the addresses start at
.33, which is the ATP500 LAN_POOL start, so almost certainly yes). The runbook assumes DHCP.

## 1. Have to hand on the day

- Console lead on the FortiGate before anything else. Step 2 of the mgmt move and the whole of
  section 3 drop SSH at some point.
- Management VLAN 1 is 192.168.1.0/24 everywhere after Tuesday, FortiGate as 192.168.1.1 (Mat,
  23 Oct evening). Switches and APs keep their addresses; the known switches are pinned by MAC in
  the FortiGate scope. The island's 192.168.201.0/24 is dropped: SW101, SW102 and SW14 become
  192.168.1.101, .102 and .114 at the start of the Tuesday window (section 3, step 2).
- Laptop on Tailscale (reaches the jump box, then both gateways), phone with Nebula.
- Google Authenticator for the ATP500 full admin (lease change on Monday).
- The printed patch map (plan v2 section 2) and this doc. The new fibres are patched into the panel
  port next to each existing run; the cabinet ends are NOT yet plugged into the cabinet switches.
- A laptop with an RJ45 port for the isolation test (section 3, step 6).
- Someone in the office to field "the internet dropped" calls; the all-tenants notice has gone out.

## 2. Monday 26 October: preparation (Mat present, about two hours)

### 2a. FortiGate management moves to 192.168.5.99 (plan step 0)

Why first: vlan10 cannot be created on the FortiGate while mgmt sits in 192.168.10.0/24.

1. Paste part 1 of `plans/2026-10-27/10-fgt-mgmt-move.txt` (adds 192.168.5.99 as a secondary
   address; nothing removed).
2. Jump box: the nmcli and tailscale lines in the same file (adds 192.168.5.98, advertises
   192.168.5.0/24). Approve the route in the Tailscale admin console. From the laptop:
   `ssh` to the box, then `bin/jb fgt "get system status"` still works on the old address, and
   `ssh ro-jumpbox@192.168.5.99` from the box answers.
3. Only when 2 is proven: paste part 2 FROM THE CONSOLE (swaps the primary address, drops the
   secondary). Then the "afterwards" lines on the jump box: new address only, old route gone,
   HOST= in `~/jumpbox-setup/fortigate-cmd.sh` and `fortigate-discover.sh`, `private/jb.env`,
   the address list in `bin/jb status`.
4. Check: `bin/jb fgt "get system interface physical"` shows mgmt 192.168.5.99 and no 192.168.10.x.
   `bin/jb status` shows the FortiGate up on the new address.

Rollback: console, `config system interface / edit mgmt / set ip 192.168.10.99 255.255.255.0`.

### 2b. Shorten DHCP leases (so Tuesday's moves settle in minutes, not days)

- FortiGate: paste `plans/2026-10-27/20-fgt-shorten-leases.txt` (vlan150 to 160 to 10 minutes).
  Clients renew within 3.5 days of their 7-day lease, so by Tuesday afternoon most hold 10-minute
  leases; those that don't, re-address when their port is bounced (section 4).
- ATP500: `ATP_OTP=<code> bin/jb atp --admin` is read-only by design; paste
  `plans/2026-10-27/21-atp500-shorten-leases.txt` yourself in an admin session. Tenant pools only.
  LAN_POOL (the switches' and APs' 192.168.1.x scope) is left alone: the FortiGate replicates that
  subnet on the aggregate (Mat, 23 Oct evening), so management devices keep their addresses.

### 2c. Nebula: VLAN tables and the island switches (plan step 2 prep, section 8)

Do these Monday because SW101, SW102 and SW14 are unreachable from Nebula for part of Tuesday
morning (section 3) and cannot be configured then.

1. Every switch (SW01, SW02, all cabinet switches, SW101, SW102, SW14): define VLANs 10 to 99.
   Fix 40, 59 and 67 properly (they only work today because the GS1920s forward undefined VLANs).
2. SW101: ports 1+2 as one LACP trunk group, PVID 1 untagged, 10-99 tagged (this is where x1 and
   x2 land on Tuesday; port 10 is x1 today and is unaffected until then). SFP 3, 4, 5, 6: trunk,
   PVID 1 untagged, 10-99 tagged (FHG, PH3, PH2, PH1). Port 11 to SW102: trunk, all VLANs.
3. SW102: SFP 1 to 5: trunk, PVID 1 untagged, 10-99 tagged (Basement, FH3, FH2, CW3, CW2).
   Port 11 to SW101: trunk, all VLANs. Port 12: trunk, VLANs 75 to 99 tagged ONLY, no VLAN 1, no
   10-74 (the interim link to SW01). Confirm SW102 reaches SW101 over port 11 today; if the two are
   linked on port 12 at the moment, move that link to port 11 first.
4. SW01: port 24 trunk, VLANs 75 to 99 tagged only (matches SW102 port 12). The cabinet uplinks on
   SW01 (p23, p25, p26, p27, p28) and SW02 (p25 to p28, p2): tagged 75-99 added, so the renumbered
   tenants can reach the trunk from their cabinets on Tuesday.
   Also SW102 SFP 6: full trunk, PVID 1 untagged, 10-99 tagged, nothing plugged in. SW01 port 25
   gets the same config on Tuesday the moment PH3 has left it (section 5, cabinet 2). These two
   ports are the permanent uplink and get plugged together at the last swap (5b); configuring them
   while empty means the swap needs no Nebula push.
5. Prove the exclusion: put a laptop on a spare VLAN (say 99) on SW01 and another on SW102 with
   the trunk NOT yet plugged; then plug SW102 port 12 to SW01 port 24 (Cat6, both ends free today)
   and check 99 passes but a 10-74 VLAN does not (laptop on VLAN 20 on SW01 side cannot ping the
   FortiGate's 192.168.20.254 once it exists on Tuesday; today: no MAC of SW102 appears in SW01's
   VLAN 20 MAC table). Leave the Cat6 plugged in: with only 75-99 allowed and nothing on 75-99 yet,
   it carries nothing.
6. SW14: nothing yet (PlanetB ports change on Tuesday after the aggregate is up). Do not change
   the island switches' IP settings on Monday; that is the first act of Tuesday's window, because
   the moment they point at 192.168.1.1 they are off Nebula until the aggregate exists.

Check from the jump box (read-only, no permission needed):
`bin/jb sw 192.168.1.39 "show vlan"` (VLANs 10-99 present), `bin/jb sw 192.168.1.39 "show lldp info remote"`
(port 24 sees SW102 once plugged), `bin/jb sw 192.168.1.39 "show mac address-table all"` (no FortiGate
aggregate MAC on any VLAN below 75).

### 2d. Patch the new fibres at the panel end only

Per the patch map. Cabinet ends stay unplugged. Nothing to check; the links come up on Tuesday.

## 3. Tuesday morning: the FortiGate side (plan step 1). PlanetB and island mgmt off for ~30 min

Start 08:00 or whenever PlanetB (FHG) agreed. Console on the FortiGate. Nothing on the ATP500 side
is touched in this section; the 44 ATP500 tenants do not notice any of it.

1. Baseline capture (read-only, from the jump box):
   `bin/jb fgt "get system interface physical"`, `bin/jb fgt "diagnose netlink aggregate list"`,
   `bin/jb fgt "get system arp"`, and `bin/jb pull` afterwards so the pre-change state is in git.
2. Nebula first, while SW101, SW102 and SW14 are still reachable over x1: set each to a static
   management address, 192.168.1.101 (SW101), .102 (SW102), .114 (SW14), mask 255.255.255.0,
   gateway 192.168.1.1, DNS 8.8.8.8, management VLAN 1. They drop off Nebula at once (no gateway
   yet) and come back in step 5. Fallback if the push misbehaves: leave them on DHCP and
   power-cycle each after step 4; the FortiGate scope reserves the same three addresses by MAC.
   Then paste `plans/2026-10-27/30-fgt-clear-x1-x2.txt`. From here PlanetB is down.
   If FortiOS says "entry is used", stop: something in the dependency list was missed; nothing is
   broken; find the reference (`show full-configuration | grep -n <name>`) and delete it first.
   The final `delete "fortilink"` may be refused; that is fine, x2 is free after `unset member`.
3. Physical, at SW101: move the FHG singlemode fibre from port 1 to SFP 3. Move x1's cable from
   port 10 to port 1. Connect x2 to port 2 (new DAC/fibre from the shopping list).
4. Paste `plans/2026-10-27/40-fgt-build-lan-bond-10g.txt`, then `41-fgt-policies.txt`. About
   4,000 lines; paste in chunks if the console buffer chokes (each `config ... end` block stands
   alone). Expect no errors. If a VLAN interface refuses because of an overlap, it means 2a did not
   finish (192.168.10.x still on mgmt).
5. Checks: `diagnose netlink aggregate name LAN-Bond-10G` (both members up, LACP bundled),
   `get system interface | grep -c LAN-Bond-10G` (90 + 1), `execute ping 192.168.1.101`, `.102`
   and `.114` (SW101, SW102, SW14 on their new addresses). Nebula shows all three online again
   (through the new mgmt policy). The aggregate's untagged side is 192.168.1.1/24, a replica of the
   ATP500's LAN1: the island VLAN 1 and the SW01-side VLAN 1 are the same subnet, joined at the
   last swap (5b). Nothing answers on 192.168.201.x any more, which is intended.
6. Isolation test, from SW102 port 12 (unplug the Cat6 from it for ten minutes, make port 12 an
   access port in VLAN 20 in Nebula, laptop on it): gets 192.168.20.x from the FortiGate, reaches
   the internet, `curl ifconfig.me` shows 193.221.132.138, cannot reach a host on the ATP500's copy
   of VLAN 20. Put port 12 back to the 75-99 trunk and re-plug the Cat6.
7. PlanetB: in Nebula, SW14 PlanetB ports PVID 70 to 87 (and any SSID tagged 70). Check
   `execute dhcp lease-list vlan87` fills up; ask PlanetB to confirm. Their outage ends here.

Rollback (before step 7): `delete LAN-Bond-10G` is refused while VLANs hang off it, so rollback is
forward: recreate vlan70 on x1 by hand (`set interface x1`, vlanid 70, 192.168.70.254/24, DHCP
.2-.253, policy vlan70 to x4) and move x1's cable back to port 10. Keep this in reserve, you will
not need it: the build is additive and the only outage is the one already accepted.

Stop point A: all of section 3 done, PlanetB back, no ATP500 tenant touched. Safe to pause here.

## 4. Tuesday mid-morning: renumber the FortiGate tenants (plan step 3)

All in Nebula; the FortiGate side already exists (vlan75-85). Order: Simon Campbell first as the
canary (one port, no fixed devices), then the rest. Per tenant:

| Old | New | Tenant | Ports today (PVID) | SSIDs |
|---|---|---|---|---|
| 160 | 85 | Simon Campbell PH1.5 | SW03 p6 | Nebula |
| 150 | 75 | Create London CW207 | SW05 p8 | Nebula |
| 151 | 76 | ReLine FH2.1 | SW06 p3 | Nebula |
| 152 | 77 | Curamcare PH2.3 | SW04 p12 (their only AP) | Nebula |
| 153 | 78 | Cake Architecture PH3.6-8 | SW12 p3-p6; SW13 p4 tagged | Nebula |
| 154 | 79 | 01-Profiles / Gunga FH2.11 | SW06 p1 | Nebula |
| 156 | 81 | Harp-E PH3.17-18A | SW13 p4 | Nebula |
| 157 | 82 | Henry Playfoot PH1.14 | SW03 p16 | Nebula |
| 158 | 83 | Fair Finance (their FortiGate side) | SW06 p10, p12 | Nebula |
| 159 | 84 | St Paul's Waldorf School PH2.13 | SW04 p8, p10 | Nebula |
| 155 | 80 | CoLab FHG1 (gone) | SW07 p12 | leave PVID; nothing on it |
| 161 | 86 | Mediorite tagged on SW03 p7 | remove the 161 tag, PVID stays 58 | none |

1. Change the PVID on the listed ports and the VLAN tag on the tenant's SSID(s) in Nebula.
2. Bounce the port (disable, enable) so wired clients re-DHCP at once. WiFi clients re-address
   within the 10-minute lease.
3. Check: `bin/jb fgt "execute dhcp lease-list vlan85"` shows the clients; a ping from the
   FortiGate to one of them answers; the tenant confirms a web page loads. Curam: ecare123.site
   loads (the whitelist policy was copied as vlan77-Whitelisting).
4. Next tenant.

Their traffic rides SW03/04/05/06/12/13 to SW01, port 24, SW102, SW101, the LAG. Egress address
is unchanged (193.221.132.138, now the whole building's shared address), so nothing outside notices.

Do NOT paste `60-fgt-retire-vlan150-175.txt` today. The old vlan15x interfaces stay until every
tenant is confirmed and the 10-minute leases have aged out (Wednesday at the earliest).

Stop point B: ten tenants renumbered, PlanetB on 87. Still no ATP500 tenant touched.

## 5. Tuesday afternoon: cabinets, one at a time (plan step 4)

Each cabinet: unplug its old uplink from SW01/SW02 FIRST, then plug the new fibre into the cabinet
switch's uplink port. Never both at once (that bridges the two gateways on every VLAN). One person
can do it; two is faster (one at the panel, one at the cabinet with a phone).

What happens to the tenants in that cabinet: their VLAN now ends on the FortiGate replica with the
same subnet and the same gateway address (.254). Clients keep their addresses; they re-ARP for
.254 within about a minute and carry on. DHCP renewals (10-minute leases) go to the FortiGate, which
either confirms the address or hands out a fresh one. Fixed-address devices (Thames Reach's firewall
at .253, Cafe OTO's router at .1, LAWA's printer at .10) need nothing. The cabinet switch and its
APs are the same story on VLAN 1: 192.168.1.1 is now the FortiGate, their addresses are reserved
for them (summary.txt), they re-ARP and stay in Nebula. A switch that drops out of Nebula for more
than a couple of minutes after a re-patch is a real fault, not expected behaviour.

Split VLANs: these have ports in more than one cabinet, so for the hours between the two swaps the
two halves sit on different gateways (same subnet) and cannot see each other. Internet works for
both. 10 (SW01, SW02, SW05, SW12, SW13), 13 (SW10, SW12), 14 (SW03, SW11), 27 (SW02, SW03),
28 (SW06, SW13), 34 (SW01, SW03), 48 (SW09, SW12), 55 (SW05, SW08), 64 (SW02, SW06, SW09).
Mat accepted this on 23 Oct; none of them is a printer-shared-across-floors case as far as the
captures show, but 10 (Bootstrap's own office) is the one to keep an eye on.

Order and what is in each cabinet (switch names per configs/switches/NOTES.md; confirm the panel
port against the patch map):

1. FHG: already on the island (SW14, done in section 3). The FHG2 GS1350 (192.168.1.46, Full Time
   Hobby 59, Silverfish 67) hangs off SW02 port 2 in the main comms room, so it moves at step 10.
2. PH3 (SW12 192.168.1.33, SW13 .45) to SW101 SFP 4. Old uplink: SW01 p25. VLANs 10, 13, 28, 29,
   32, 48, 53, 56, 72 and renumbered 78, 81. Straight after: in Nebula, SW01 port 25 becomes a full
   trunk (PVID 1 untagged, 10-99 tagged) while it sits empty; its SFP module stays in. That is the
   permanent uplink from SW102 SFP 6, plugged in at step 10.
3. PH2 (SW04 .35) to SW101 SFP 5. Old uplink: SW01 p26. VLANs 24, 36, 67, 69 (LAWA printer
   reservation .10), 77, 84.
4. PH1 (SW03 .47) to SW101 SFP 6. Old uplink: SW01 p27. VLANs 14, 20, 27 (DGN), 34, 51, 52,
   58 (Mediorite), 62, 73, 74, 82, 85. Then paste `plans/2026-10-27/50-fgt-mediorite-vip.txt`
   and ask Anthony to test a NinjaOne connection to 193.221.131.34.
5. Basement (SW15 .37) to SW102 SFP 1. Old uplink: SW01 p28. VLANs 17 (taproom), 46, 66.
6. FH3 (SW09 .44, SW10 .42, SW11 .43) to SW102 SFP 2. Old uplink: SW02 p25. VLANs 13, 14, 45, 48, 64.
7. FH2 (SW06 .34, SW07 .40) to SW102 SFP 3. Old uplink: SW02 p26. VLANs 16 (Fair Finance), 28, 35,
   64, 76, 79, 83, and the Cisco pair on 16.
8. CW3 (SW08 .36) to SW102 SFP 4. Old uplink: SW02 p27. VLANs 12, 21, 26, 39, 41, 44, 50,
   54 (Thames Reach: VIP .35 live from this moment; ask Akos to test), 55.
9. CW2 (SW05 .41) to SW102 SFP 5. Old uplink: SW02 p28. VLANs 10, 18, 37, 38, 49, 55, 60, 70
   (Leaders Unlocked), 75.
10. Main comms room, the last swap: SW01 and SW02 themselves (VLANs 10, 11, 34, 42 on SW01;
    27, 64, 65, 71 Cafe OTO and the FHG2 switch on SW02). This one is different, read 5b.

Per cabinet, after plugging in:
- Nebula: the SW101/SW102 port shows link up at 1G (the cabinet switches have 1G SFP uplinks).
- `bin/jb fgt "get system arp"` grows with that cabinet's subnets; `execute ping` one host per VLAN.
- Phone a tenant in the cabinet, or load a page from the cabinet's AP. The cabinet switch and its
  APs stay in Nebula on their 192.168.1.x addresses throughout.
- Then the next cabinet. Rollback for any cabinet is the same re-patch reversed.

Stop point C: after any cabinet. The remaining cabinets simply stay on the ATP500 until done.

### 5b. The main comms room swap (SW01 port 2)

The ATP500's only LAN link is SW01 port 2. SW01 and SW02 are not re-patched; they stay, and from
this moment reach the FortiGate over the permanent fibre, SW102 SFP 6 to SW01 port 25, carrying
VLAN 1 and 10-99 (both ends configured earlier while empty, so no Nebula push is needed now). The
interim Cat6 on port 24 (75-99 only) has done its job and comes out. Three cable moves, in this
order, within a minute, all in the comms room:

1. SW01 port 2 out (the ATP500 ge4 cable). SW01-side tenants and VLAN 1 have no gateway for the
   next few seconds.
2. SW01 port 24 Cat6 out. It must come out before the fibre goes in: two live links between the
   same two switches would loop on 75-99.
3. Fibre from SW102 SFP 6 into SW01 port 25. Done: every tenant is on the FortiGate, and VLAN 1 is
   one subnet (192.168.1.0/24) across the whole building with the FortiGate as 192.168.1.1.
4. SW01, SW02, the FHG2 switch, the APs and the Cisco pair keep their addresses, re-ARP for
   192.168.1.1 and stay in Nebula. Cafe OTO's VIP .36 is live now; ask James to test.
5. Checks: Nebula shows SW01 port 25 up at 1G with SW102 as LLDP neighbour, port 24 down;
   `bin/jb fgt "get system arp"` shows every live subnet plus the 192.168.1.x switches;
   `bin/jb atp "show arp"` (USB NIC, still up) shows nothing new arriving on the ATP500. The jump
   box's own path to `bin/jb sw 192.168.1.39` went with the ATP500 link; it comes back once the box
   has a route via the FortiGate mgmt leg (section 7).

Rollback: fibre out of port 25, Cat6 back into port 24, ATP500 back into port 2 (that order).

## 6. End of day

- `bin/jb pull` for a full capture of the FortiGate as built; commit.
- Note in Nebula which cabinets are done. Anything not done stays on the ATP500 safely.
- Leave the ATP500 running and the ATP500-side management (USB NIC, 192.168.254.x) alone.

## 7. Later in the week, not Tuesday

1. Wednesday or after, once every renumbered tenant is confirmed and no client still holds a
   192.168.15x address (`execute dhcp lease-list vlan150` empty): paste
   `plans/2026-10-27/60-fgt-retire-vlan150-175.txt`. Also removes ReLine's dead VIP, the CoLab
   whitelist, vlan101/102 relics. Then in Nebula, remove the tagged 150-175 from SW01 ports 9+10
   and the cabinet uplinks.
2. Nebula tidy: SW01 port 24 and SW102 port 12 lose the 75-99 trunk config; SW102 port 12 joins
   the SW101-SW102 LAG on 11+12.
3. SW02 retirement: its remaining local ports (p1 DGN 27, p2 FHG2 switch, p4/p5 Dusty Knuckle,
   p6 65, p7 Cafe OTO) re-home to free SW01 ports, then SW02 comes out. Separate small job.
4. ATP500 off after a quiet week: paste `plans/2026-10-27/70-fgt-final-cleanup.txt` (LAN-Bond-2
   goes, port3/port4 free). Decide what the jump box's USB NIC and the 192.168.254.0/24 Tailscale
   route do next (Mat's call, Mat present).
5. Jump box reach to the switches: still 192.168.1.x, but the path was through the ATP500. A static
   route on the box via the FortiGate mgmt leg needs a policy mgmt to LAN-Bond-10G on the
   FortiGate; or Nebula only. Decide after the dust settles.
6. Repo: FACTS.md (gateway table, VLAN table, mgmt address, jump box), configs/fortigate/NOTES.md,
   configs/switches/NOTES.md (new uplinks, SW02 gone), notes/MEMORY.md, jumpbox-setup/README.md.
   Re-run the crossref after the capture.

## 8. If something goes wrong: the short list

- A tenant has no internet after their cabinet moved: is it a fixed-IP device with the wrong
  gateway? (gateway is .254 on every VLAN, unchanged). Is the VLAN inactive on the sheet and so
  has no policy? (summary.txt "active" column; add a policy by copying any vlanNN block in
  41-fgt-policies.txt). Is it a webfilter block? (FortiGate log, policy's webfilter profile).
- A renumbered tenant still has a 192.168.15x address: bounce their port; worst case 10 minutes.
- A cabinet switch drops out of Nebula after its re-patch: its VLAN 1 is not reaching the
  FortiGate. Check the SW101/SW102 port is PVID 1 untagged, and that 192.168.1.1 answers from the
  FortiGate (`execute ping 192.168.1.39` from the FortiGate once SW01 is over). Temporary fix is the
  old uplink back in.
- FortiGate paste error "entry is used" or "overlap": stop, read the line, nothing partial is
  committed inside that object. The generator order is dependency-safe when pasted in file order.
- Everything: rollback per section. The ATP500 is untouched all day except lease times.
