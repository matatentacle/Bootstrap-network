# WAP recommendations Mat has already given Bootstrap

Where the earlier WiFi advice lives, so it is not re-invented. Compiled 23 Oct 2026 from Mat's
sent mail and Drive.

## 1. "AP Settings", 23 Oct 2025, to Shopna (thread "Re: Nebula Access")

Sent as AP Settings.pdf. Source is the Google Doc "AP Settings" in Mat's Drive
(docs.google.com/document/d/11lXLuF4FnoXtzHUH8qDBj2gXS7g75i16puSYqZkx3gQ). Written after a light
physical survey of the CoLab space with Nebula write access.

What was changed: per-device rate limits on the CoLab and Cake Architecture APs removed. Reason
given: APs "fighting" the limit caused drops, lag and lower throughput; the building already had
caps at the switch ports, and longer term caps should be VLAN-based shaping on the firewall.

CoLab recommendations:
- Two APs, not one; place them where the switched-off TP-Link APs are, those are good coverage spots.
- Replace the Zyxel GS-105B v5 with a small Zyxel PoE switch (about 40 pounds) so the APs run on
  one cable each.
- Existing cables fine; one new run to the second AP; any standard cable, no shielding benefit.
- Longer term: a small comms cabinet at the back of the meeting room, repurposing an underused
  switch, linked to Dupe's comms cab, so heavy users can go wired and free AP capacity.

Companion doc the same day, "Collab Wifi" (docs.google.com/document/d/1RrhhyCHXzHOWrqXnrQfZG8LcwLUTJxjSVuzx03ncRWw):
81 Nebula devices then (19 switches, 62 APs); standard AP NWA1123ACv3 with a scattering of NWA50AX
and NWA1123-AC HD; correlation noted between per-client clamping at the AP and instability;
SSID VLAN set to 1 while the AP's assigned VLAN was 153/155 on CoLab and Cake (harmless with one
SSID and matching PVID, flagged for consistency).

Shopna's reply the same day: Cake Architecture (PH3.6-8, SW12 ports 3/4) had connection speed
issues and "a lot of interference on 5 GHz".

## 2. Infrastructure audit list, 20 Apr 2026, to Dani, cc Shopna, Asim, Halim (thread "Re: Fortigate x Bootstrap network move")

Seven points. The WAP-related ones:
- Point 1: switch-port bandwidth caps with no gateway shaping cause packet drops, TCP retransmit
  loops and saturation as the office fills up; fix is shaping policies on the gateway in three
  pre-built tiers. (Same finding as `switch-port-caps-2026-10-23.md`.)
- Point 3: many ports left as trunks with stale VLANs, suspected from assigning WAPs to a space
  and then changing the client, or running several SSIDs off one WAP; default should be access
  ports on the PVID.
- Point 5: restructure the master spreadsheet into a client sheet (client, VLAN, WAP if any,
  notes) and a room reference sheet.

## 3. Other threads touching WiFi

- "Fair Finance network issues", 28 Oct 2025: Mat offered half a day to get their WiFi on and
  asked for the make of their AP.
- "Network Infra overhaul", 12 Jan 2026: kit order for the racks (about 350 pounds ex VAT), ordered
  by Halim 13 Jan.
- "Zyxel Networks AVOIP/Range", 16 to 23 Oct 2026: Mark Richards (Zyxel) and Resay finance
  introduction, about 2,700 pounds of educational licensing over four years; quotes pending.

## Standard AP going forward (Mat, 23 Oct 2026)

The step up from the NWA50AX is the **Zyxel NWA90AX Pro** (part NWA90AXPRO-EU0102F), bought
from Broadband Buyer: https://www.broadbandbuyer.com/products/49293-zyxel-nwa90axpro-eu0102f/
WiFi 6 dual-band 2x2 with a 2.5GbE uplink, 802.3at PoE, Nebula-managed like the rest of the
estate. Two are already in the building (LLDP, 23 Oct 2026):
- Cake Architecture, PH3.6-8: SW12 port 5, VLAN 153, 192.168.153.14, Nebula name "NWA90AX-PRO".
- LAWA, PH2 main office: SW04 port 7, VLAN 69, 192.168.69.4, Nebula name "MainOffice". LAWA's
  other two APs are still older units: "PH2.4-5WIFI" NWA50AX on port 3 (.69.5) and
  "PH2.12MeetingRoom" NWA1123ACv3 on port 13 (.69.6).
Price not captured here (the site refuses automated fetches); check the listing when ordering.
Use this where a tenant complains about WiFi on a single NWA50AX (Curam PH2.3, ReLine FH2.1 and
2.14, see `curam-wifi-2026-10-23.md`) and for any new AP.

## AP inventory by model (live LLDP on 14 switches, 23 Oct 2026 evening)

NWA50AX, eleven units (candidates for the NWA90AX Pro):

| Switch:port | Nebula name | Address | VLAN | Tenant |
|---|---|---|---|---|
| SW12:1 | PH3.2-TrainingRoom | 192.168.10.18 | 10 | Bootstrap (Newton Dunbar training room; the AP the therapy block used to piggyback on) |
| SW06:3 | FH2.1WIFI | 192.168.151.10 | 151 | ReLine, FH2.1 and 2.14 |
| SW04:3 | PH2.4-5WIFI | 192.168.69.5 | 69 | LAWA, PH2.4-5 |
| SW04:6 | PH2.11WIFI | 192.168.36.10 | 36 | Oscar Deen Eyewear, PH2.11 |
| SW04:12 | PH2.3 | 192.168.152.18 | 152 | Curam, PH2.3 |
| SW08:5 | CW304 | 192.168.44.3 | 44 | VBQ Speakers / Ryan Oxley, CW304 |
| SW05:8 | CW207WIFI | 192.168.150.10 | 150 | Create London, CW207 |
| SW13:4 | PH3.17-18WIFI | 192.168.156.10 | 156 | Harp-E, PH3.17-18 |
| SW03:1 | PH3.6-8WIFI | 192.168.52.1 | 52 | Nordicity, PH1.1 (AP still carries Cake's old room name; probably moved when Cake got the Pro) |
| SW03:14 | PH1.13WIFI | 192.168.62.1 | 62 | Teim Accountants, PH1.13 |
| SW03:16 | PH1.14WIFI | 192.168.157.10 | 157 | Henry Playfoot, PH1.14 |

NWA90AX Pro, two: Cake (SW12:5) and LAWA MainOffice (SW04:7).
NWA1123-AC-HD, three: SW01:1 (192.168.10.20, Bootstrap), SW03:10 (192.168.51.3, Full Circle Psy),
plus the one on the bar switch (vlan46, not read).
NWA1123ACv3: the rest, about 25, including the new therapy block AP "PH3.10AP" on SW12:2 (so the
therapy block got a 1123, not a 50AX).
Tenant-owned, not Zyxel: Compost Creative Meraki MX68 (SW08:1), a UniFi UAP-AC-Pro on SW08:22
(192.168.80.11, Studio11), Dusty Knuckle's Omada switch (SW02:5), Panasonic SIP phone (SW04:10).
SW15 (basement, 192.168.1.37) returned no LLDP detail; GS1350s and Cisco pair not read.

## Not found

No email or document in which Mat recommends specific replacement AP models or an AP count per
tenant beyond the CoLab "two APs" advice. If that conversation happened, it was verbal or on
another channel.
