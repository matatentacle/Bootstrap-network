> ARCHIVED 2026-10-13. Superseded by README.md in the parent folder and /srv/configs/*/NOTES.md.
> Statements below that turned out to be WRONG or outdated:
> - FortiGate tenants are VLANs 150 to 175 on the port3+port4 1G LACP bond, not "150 to 157" on a 10G uplink.
> - FortiGate model, firmware and serial are now known: FortiGate-120G, 7.4.12, FG120GTK24015905.
> - x2 exists but is a member of the FortiLink aggregate with x3, not a free port.
> - The ATP500 DHCP reservation for the jump box is NOT in place; it holds .100, not .10.
> - "Working rules" mention an enp3s0 link to the ATP500; it is the USB NIC (enx503eaacea0c4) that goes to the ATP500. enp3s0 goes to the FortiGate.
> - Stage 2 was done with NetworkManager (the box's renderer), not a netplan file. Profile "fortigate-mgmt".
> - The FortiGate console lead described as "connected" has never been seen on the jump box USB bus.
> - The still-valid rules (read-only on both gateways, no reboots, keep the box reachable, outputs to /srv/configs) are carried into README.md.

# Handover: Bootstrap jump box (MINI-PC-6)

Written 13 Oct 2026 for the Claude session running on the jump box itself. Mat is the operator; he supplies credentials in-session. Nothing here is permission to change either gateway's configuration.

## Working rules (read first)

- No reboots, no re-addressing, no interface changes on the FortiGate or the ATP500. Eight live tenants on the FortiGate, about 44 on the ATP500. Read-only commands only unless Mat says otherwise for a specific change.
- Keep this box reachable. Never touch Tailscale, ufw's `tailscale0` allow rule, or the `enp3s0` link to the ATP500 without `netplan try` and Mat watching.
- No FortiGate `maintainer` account recovery. It needs a reboot.
- The box has 1.8 GB RAM and a Celeron J1800. No heavy tooling, no containers.
- Save command output to `/srv/configs` rather than pasting large dumps into chat.

## The box

- Ubuntu 22.04, terminal only. Tailscale 100.83.139.20, Tailscale SSH on. ufw: deny incoming, allow outgoing, everything allowed on `tailscale0`.
- `picocom` and `minicom` installed.
- NICs:
  - `enx503eaacea0c4` (TP-Link UE300 USB): cabled to ATP500 port P7 (`ge7`). DHCP from the ATP500, subnet 192.168.254.0/24, gateway 192.168.254.1. A reservation to 192.168.254.10 may be in place; verify. This is the only link with internet egress and carries Tailscale.
  - `enp3s0` (onboard): direct cable to the FortiGate management interface, nothing else on that link. FortiGate is at 192.168.10.99, static, no DHCP. Not yet addressed on our side.
- Console: one FTDI USB-to-RJ45 lead connected to the FortiGate console (9600 8N1). The ATP500 console lead (115200 8N1) is not cabled yet.

## The gateways

ATP500 (old, being retired)
- Management from this box: 192.168.254.1 (its `ge7` address). HTTPS on port 50483, SSH on 22. Both currently accept from every zone.
- Accounts: `MKennedyAdmin` (admin) and `Mat-Kennedy` (limited-admin). Both enforce Google Authenticator 2FA on web and SSH, so interactive only. Mat enters the code.
- Firmware 5.43(ABFU.0), hostname `atp500`. Startup config from today exists on Mat's machine; he will copy it over.
- Known quirks: secure-policy 3 "Webaccess" is an allow-any rule and makes every deny below it dead. Scheduled reboot every Monday 04:00. Cloud-helper firmware auto-update with reboot every Sunday 00:00. Weekly config backup emailed Mondays. Do not fix any of this now; it is logged for the lockdown phase.

FortiGate (new, Vorboss line)
- Management interface 192.168.10.99. Model, firmware, serial and interface map not yet recorded. This is the first thing to capture.
- Previously only a read-only account. Console access exists and may give full admin; find out.
- Public IP 193.221.132.138, secondary subnet 193.221.131.32/27. Tenants on VLANs 150 to 157. Uplinked on one 10G port to Zyxel backbone switch 101 port 10.
- Address overlap, accepted for now: 192.168.10.0/24 is also Bootstrap's own VLAN 10 on the ATP500. The FortiGate link is a direct cable with no default route, so it is harmless. Consequence: this box cannot route to ATP500 VLAN 10 hosts while that link is up. Fix later by moving the FortiGate management subnet.

## Stage 1: confirm state

```
ip -br addr
ip route
tailscale status
tailscale netcheck
sudo ufw status verbose
ls -l /dev/serial/by-id/
cat /etc/netplan/*.yaml
```

Expected: default route via 192.168.254.1 on `enx503eaacea0c4`, `netcheck` showing a DERP table, one FTDI device under `/dev/serial/by-id/`.

## Stage 2: address the FortiGate link

Static on the onboard NIC, no default route. Direct cable, so .98 is free by definition. Create `/etc/netplan/60-fortigate-mgmt.yaml`:

```yaml
network:
  version: 2
  ethernets:
    enp3s0:
      dhcp4: false
      addresses: [192.168.10.98/24]
```

If the existing netplan file already has an `enp3s0` stanza with `dhcp4: true`, change that stanza instead of adding a second file, so the two do not conflict.

Apply with rollback:

```
sudo chmod 600 /etc/netplan/60-fortigate-mgmt.yaml
sudo netplan try
```

Confirm, then test:

```
ip route
ping -c 3 192.168.10.99
curl -k -sI https://192.168.10.99 | head -5
```

`ip route` must still show the only default via 192.168.254.1. If a second default appears, stop and fix the file before pressing Enter.

Leave `enx503eaacea0c4` on DHCP for now. Pin it static later once Mat confirms the reservation.

## Stage 3: FortiGate discovery (read only)

Over SSH once Mat gives the account:

```
ssh <account>@192.168.10.99
get system status
get system interface physical
show system interface
get system performance status
get hardware nic <name>
show full-configuration
```

Over the console if SSH is read-only or blocked. Log the session:

```
mkdir -p /srv/configs/fortigate
sudo picocom -b 9600 --logfile /srv/configs/fortigate/console-$(date +%F).log /dev/serial/by-id/<ftdi-device>
```

Exit picocom with Ctrl-A then Ctrl-X. Press Enter once connected to get a login prompt.

Record in `/srv/configs/fortigate/NOTES.md`: model, firmware, serial, which physical port is the 10G uplink, which ports are free, whether `x2` exists, which interface holds 192.168.10.99, and which admin accounts exist with their trusted hosts (`show system admin`).

## Stage 4: config repo

```
sudo mkdir -p /srv/configs && sudo chown $USER:$USER /srv/configs
cd /srv/configs
git init
mkdir -p atp500 fortigate
```

- ATP500: Mat copies today's `startup-config.conf` into `atp500/`. Later dumps come from SSH: `show running-config` after 2FA login.
- FortiGate: `show full-configuration` saved to `fortigate/full-config-$(date +%F).conf`.
- Add a `README.md` with both serial numbers once known. Commit.

Credentials never go in the repo. The ATP500 config contains password hashes only, which is acceptable; the FortiGate config may contain encrypted secrets, same standing.

## Stage 5: ser2net and udev (when both console leads are cabled)

Identify each FTDI lead by serial:

```
udevadm info -a -n /dev/ttyUSB0 | grep -m1 'ATTRS{serial}'
```

`/etc/udev/rules.d/99-console.rules`:

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{serial}=="<fortigate-lead-serial>", SYMLINK+="con-fortigate"
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{serial}=="<atp500-lead-serial>", SYMLINK+="con-atp500"
```

`sudo udevadm control --reload && sudo udevadm trigger`, then check `/dev/con-*` exist.

`/etc/ser2net.yaml` (install with `sudo apt install ser2net`):

```yaml
connection: &fortigate
  accepter: tcp,100.83.139.20,2001
  connector: serialdev,/dev/con-fortigate,9600n81,local
  options:
    kickolduser: true

connection: &atp500
  accepter: tcp,100.83.139.20,2002
  connector: serialdev,/dev/con-atp500,115200n81,local
  options:
    kickolduser: true
```

`sudo systemctl enable --now ser2net`. Binding to the Tailscale address means only tailnet peers reach the consoles. From any tailnet machine: `telnet 100.83.139.20 2001`.

## Not in scope for this session

- Any change to WAN-side admin access on either gateway.
- Service-control or trusted-host changes. Those come after both consoles are proven.
- Adding P7 or P8 to the ATP500 LAN1 port group (trunk auditing). That touches the group carrying 44 VLANs and needs a window.

## Still to find out

- FortiGate model, firmware, serial, free ports, `x2` presence.
- Whether console login on the FortiGate is full admin.
- Whether the ATP500 DHCP reservation for `enx503eaacea0c4` is in place.
