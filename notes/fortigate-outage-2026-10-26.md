# FortiGate-120G down, Mon 26 Oct 2026 (recovered 13:04Z; cause: console lead held it at the BIOS menu)

**Recovered.** At 13:14Z Mon 26 Oct the FortiGate answered on 192.168.10.99 with uptime 10 minutes,
so FortiOS came up at about 13:04Z. Last reboot reason "power cycle". mgmt, port3, port4 (1G) and
x1, x4 (10G) all up; SW01 ports 9 and 10 back at 1G/F; ping 8.8.8.8 from the box 1 ms, 0 loss;
2,000 sessions and 75 Mbps within ten minutes, so tenants are passing traffic. Downtime: Sat 24 Oct
15:09Z to Mon 26 Oct 13:04Z, about 46 hours.

**Cause (Mat, 26 Oct 13:30Z):** a console cable of the wrong type was plugged into the FortiGate's
console port. Mat unplugged it and the unit booted. This is a documented FortiGate behaviour: any
character or break on the console during the first seconds of boot answers the BIOS "Press any key
to display configuration menu" prompt, and the unit then sits in the BIOS menu and never loads
FortiOS. A wrong-pinout lead or an idle USB-serial adapter can hold the line in that state. It
explains everything: the box ran 31 days with the lead in place (no reboot, so no harm), the mains
dip rebooted it into the menu, the 10:44Z power cycle did the same, and removing the lead let the
next boot through. Not a hardware fault. No RMA needed. Fortinet offers a BIOS "restricted mode"
where only Ctrl+B opens the menu and stray input is ignored; worth enabling before any console
lead goes on the jump box (a config change, needs Mat's OK). Rule from now: no console lead left
on the FortiGate unattended. Mat (26 Oct 13:40Z): the lead had been in for about a week, so it was there through the
Saturday dip and the Monday power cycle. Replaced the same day with a Prolific PL2303 USB lead on the
jump box (/dev/ttyUSB0, tentacle in dialout); proven from the box at 13:45Z, Enter returns the login
prompt. Mat would rather test a reboot with the new lead in, at a quiet moment, than enable BIOS
restricted mode straight away.

Status before recovery:

Status at 12:15Z Mon 26 Oct: FW-120G-01 has PWR lit, STATUS off, mgmt port link lit. It does not
answer ARP on 192.168.10.99 (so FortiOS is not running, this is not a blocked ping). SW01 ports 9
and 10 (its LAN LAG, port3+port4) have no link. WAN 193.221.132.138 answers neither ping nor TCP
443 from the internet (HTTPS admin is normally open there). Mat power-cycled it at 10:44Z today;
same result. Eight FortiGate tenants (VLANs 150 to 161) and PlanetB (vlan70 via x1) have no internet.

## Timeline (UTC; UK was BST, UTC+1, until 01:00Z Sun 25 Oct)

| When | Evidence | What |
|---|---|---|
| Fri 23 Oct 18:30 to 19:18 | SW01 log: config saves, admin logins from the box | Switch port-caps work |
| Fri 23 Oct 19:55 to 19:58 | jb captures: FortiGate port3/port4 NIC, ARP, vlan151 | Last FortiGate session on record. Mat also in the GUI late that evening (Mat's recollection) |
| Sat 24 Oct 15:09:46 | jump box kernel log: enp3s0 link down, up again 15:09:50 | FortiGate mgmt PHY reset for 4 s |
| Sat 24 Oct 15:08 to 15:11 | SW01 log: "System cold start", "System has reset without management command", NTP sync 15:11:37 | SW01 power loss and cold boot |
| same minute | uptime 45:01 h at 12:10Z Mon on .38 .39 .41 .42 .43 .44 .45 .47 | eight switches cold-booted together |
| after that boot | SW01 log shows ports 1, 2, 16, 23, 25 to 28 coming up; never 9 or 10 | FortiGate LAG never returned |
| Sat 24 Oct 23:02 to 23:08 | SW01 log: port 2 (ATP500 uplink) down/up; box: ATP500 leg carrier off 5.5 min; ATP500 uptime 1d 13:07 at 12:11Z Mon | ATP500 restarted (cause unknown). FortiGate mgmt link did not flap, so no second power loss |
| Mon 26 Oct 10:44:11 to 10:45:16 | jump box: enp3s0 down 65 s | Mat's power cycle |
| Mon 26 Oct about 13:04 | get system status 13:14Z: uptime 10 min, reason "power cycle" | FortiOS back; all expected ports up, WAN reachable, tenants passing traffic |

Not affected: jump box (up 12 days), switch 192.168.1.40 (up 4378 h). 192.168.1.46 did not answer
the uptime query at 12:10Z (check).

## Reading

A mains dip of a few seconds at 16:09:46 BST on Saturday 24 Oct hit most of the building. The
switches rebooted and came back. The FortiGate lost power too (its PHY reset) and did not boot
FortiOS. A full power cycle on Monday did not clear it. The reading at 12:15Z was boot flash or
PSU/board damage; the actual cause (see top) was a console lead holding the BIOS at its boot menu,
which looks identical from the outside: PWR on, STATUS off, mgmt PHY link lit, no ARP. The lit
mgmt link LED is the PHY only; it lights before the OS loads.

The FortiGate was working on Friday evening (23 Oct) and has been down since Saturday afternoon.
Nobody noticed over the weekend.

## Support cover and identifiers (found 26 Oct 2026, from captures and Mat's mailbox)

Identifiers for any Fortinet ticket:

| Item | Value | Source |
|---|---|---|
| Model | FortiGate-120G | get system status, 13 and 23 Oct |
| Serial | FG120GTK24015905 (TK24 = 2024 build) | same |
| System part number | P28808-04 | same |
| BIOS | 06000104 | same |
| Firmware | FortiOS 7.4.12 build 2902, auto-upgraded 12 May 2026 | same; config system federated-upgrade |
| Hostname / alias | FW-120G-01 / FortiGate-120G | same |
| FortiCare Registration Level | Enforce (firmware setting, not proof of registration) | same |
| FortiGuard contracts | antispam, outbreak prevention, web filter all "Contract", expire **Sun 16 Jan 2028** | get system fortiguard, 23 Oct |
| FortiToken Mobile licence | EFTM005131045776 (paid, 5 tokens) plus trial FTMTRIAL0A415DD3 | config user fortitoken |
| Setup date | about Jan 2025: user "asim" created 28 Jan 2025, trial tokens expired 30/31 Jan 2025 | full config |

What this means:

- A paid FortiGuard bundle is on the unit to 16 Jan 2028. A 3-year term from mid Jan 2025 fits
  the setup date. FortiGuard bundles (UTP, ATP, Enterprise) are sold with FortiCare Premium
  support, which carries hardware replacement (RMA). So the unit is very likely under FortiCare to
  Jan 2028, but nothing in the captures states the FortiCare level or expiry, and there is no
  capture of the licence widget or `diagnose debug vm-print-license` equivalent for hardware.
- The plain hardware warranty is 365 days from registration (Fortinet EULA), so it ran out around
  Jan 2026. An RMA therefore rests on the FortiCare contract, not the warranty.
- The device is registered to a FortiCloud account we do not hold. The config's only email is
  asim@mitsuk.com (user "asim", FortiToken 2FA). Shopna wrote to Mat on 26 Oct 2026: "The
  Fortigate firewall licence is with Asim." Asim Tahir (asim@mitsuk.com, support@mitsuk.com,
  company Mitsuk) set the unit up and handed Mat super-admin on 19 Oct 2026. Nothing about a
  FortiCloud account, contract or invoice is in Mat's mailbox or Drive.
- Fortinet opens RMA tickets only from the FortiCloud account the serial is registered to. A
  transfer to another account needs the current master account to do it (GUI "Transfer FortiGate
  to Another Account", or a transfer token), or a Fortinet Customer Service ticket that goes back
  to the registered owner for approval. Proof of purchase helps the Customer Service route.
- The RMA ticket itself needs: serial, fault description, what was tried (console output, HQIP
  if it boots that far), shipping address, and someone on site with a console lead for TAC's
  validation. After replacement the contracts move to the new serial via "RMA transfer" in the
  portal.

So the two things to get from Asim, today: (1) the FortiCloud account email the serial is
registered under and the FortiCare level and end date shown on the portal, (2) either he opens
the RMA ticket for Bootstrap, or he transfers the device to a Bootstrap-owned FortiCloud account
(Mat creates one first, e.g. on a Bootstrap address) so Mat can. From Shopna: the invoice for
the firewall and its licence (from Mitsuk or whoever sold it), which is the proof of purchase if
Asim does not respond and Customer Service has to be asked.

Sources: Fortinet EULA warranty terms (fortinet.com/corporate/about-us/legal), FortiCare RMA
guides and the transfer-device doc (docs.fortinet.com, community.fortinet.com).

## Next steps

1. Done 26 Oct: the cause was the console lead (see top). The console procedure below stays as
   the recipe for next time: console from a laptop, 9600 8N1, power-cycle while watching.
   - No BIOS banner at all: hardware. RMA, serial FG120GTK24015905.
   - BIOS banner then menu: unplug whatever is on the console, or choose Q to continue the boot.
     B boots the backup firmware. Never F (format) without a TFTP firmware image ready.
   - Backup partition carries an older config. Full raw capture of 13 Oct is in
     private/configs-raw/fortigate/ for restore to the same serial. Anything Mat changed in the
     GUI on Friday 23 Oct evening is not in any capture; take a fresh full capture now.
2. The 27 Oct cutover can run as written. The new lead stays on the jump box; it has not yet been
   through a FortiGate boot. Mat's plan: a reboot test with the lead in at a quiet moment, and only
   then decide on BIOS restricted mode. Until that test, pull the lead before any planned reboot.
3. Find out why the ATP500 restarted at 00:03 BST Sunday 25 Oct if Mat did not do it.
4. UPS for the comms room goes on the shopping list; eight switches and the gateway dropped on one dip.
5. Support cover, no longer urgent: still ask Asim for the FortiCloud account and FortiCare level
   and end date, and ask Shopna for the purchase invoice (see "Support cover" above), so the next
   fault does not start from zero.
