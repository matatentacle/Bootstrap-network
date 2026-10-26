#!/usr/bin/env python3
"""Generate the FortiGate (and two small ATP500) CLI blocks for migration plan v2.

    python -I plans/gen-fortigate-cli.py            writes plans/2026-10-27/*.txt

Inputs are the committed, sanitised captures only:
    configs/atp500/running-config-2026-10-13.conf      ATP500 VLANs, DHCP pools, BWM caps
    configs/fortigate/full-config-2026-10-13.conf      FortiGate vlan15x interfaces, DHCP, policies
    configs/bootstrap-records/workbook-2026-10-07/VLANS_-_FORTIGATE.csv   FortiGate client names

Rules applied (notes/migration-plan-v2-2026-10-23.md, decided by Mat 23 Oct 2026):
  - every VLAN 10 to 99 is created as a child of aggregate LAN-Bond-10G, 192.168.N.254/24
  - ATP500 VLANs keep their ID; FortiGate 150-160 -> 75-85, 161 -> 86, PlanetB -> 87, 162-175 -> 88-99
  - active tenants get a client name (alias <= 25 chars, long form in description); inactive and
    spare VLANs get no name, no policy
  - DHCP scopes copied from the device that serves the VLAN today; ATP500 "infinite" leases become
    7 days; ranges are clamped to .253 so the gateway address is never in a pool
  - bandwidth caps: ATP500 BWM "inbound guarantee" (download) -> FortiGate interface outbandwidth,
    "outbound" (upload) -> inbandwidth, both kbps. FortiGate tenants keep their outbandwidth
  - everyone egresses via the WAN address 193.221.132.138 (plain NAT, no pool), as the live FortiGate
    tenants do today; only Thames Reach and Cafe OTO get one-address pools + 1:1 VIPs, Mediorite keeps VIP .34
  - Mediorite: MEDIORITE_ON_58 below (recommended True: stay on VLAN 58, repoint VIP .34)
  - management VLAN 1: the aggregate's untagged side is a replica of the ATP500's 192.168.1.1/24
    (LAN_POOL scope + reservations for the known switches); 192.168.201.0/24 is dropped, the island
    switches move to 192.168.1.101/.102/.114 (Mat, 23 Oct 2026 evening)

Nothing here talks to a device. Mat reads the output and pastes it from the console or
bin/jb shell. The pre-commit hook scans plans/ like everything else.
"""
import csv
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ATP = os.path.join(ROOT, 'configs', 'atp500', 'running-config-2026-10-13.conf')
FGT = os.path.join(ROOT, 'configs', 'fortigate', 'full-config-2026-10-13.conf')
SHEET = os.path.join(ROOT, 'configs', 'bootstrap-records', 'workbook-2026-10-07', 'VLANS_-_FORTIGATE.csv')
OUT = os.path.join(ROOT, 'plans', '2026-10-27')

# ---------------------------------------------------------------- decisions (edit here, re-run)
AGG = 'LAN-Bond-10G'
WAN = 'x4'
NEW_MGMT_FGT = '192.168.5.99'
NEW_MGMT_JB = '192.168.5.98'
# Public addresses, decided by Mat 23 Oct 2026 (quoted in the tenant letters). One shared address for
# everyone unless a tenant asked otherwise: the FortiGate's WAN address, which the live FortiGate tenants
# already use (Curam's ecare123 allow-list and possibly Cake/Reline depend on it), so no pool at all.
SHARED_EGRESS = '193.221.132.138'                                     # x4 interface address, no ippool
POOL_TR = ('POOL-ThamesReach', '193.221.131.35', '193.221.131.35')   # Thames Reach, was 157.231.128.136
POOL_OTO = ('POOL-CafeOTO', '193.221.131.36', '193.221.131.36')      # Cafe OTO, was 157.231.128.140
VIP_TR = ('VIP-193.221.131.35-ThamesReach', '193.221.131.35', '192.168.54.253')
VIP_OTO = ('VIP-193.221.131.36-CafeOTO', '193.221.131.36', '192.168.71.1')
OTO_SERVICE = ('CafeOTO-1000-2000', '1000-2000')
MEDIORITE_ON_58 = True          # True: Mediorite stays on VLAN 58, VIP .34 -> 192.168.58.3; VLAN 86 is a spare
MEDIORITE_HOST_58 = '192.168.58.3'
MEDIORITE_HOST_86 = '192.168.86.250'   # only used when MEDIORITE_ON_58 is False
SHORT_LEASE = 600               # seconds, FortiGate vlan150-160 before renumbering
ATP_SHORT_LEASE = '0 0 10'      # ZLD "lease D H M": 10 minutes, ATP500 pools before cutover
INFINITE_LEASE_BECOMES = 604800
RENUMBER = {v: v - 75 for v in range(150, 176)}    # 150->75 ... 175->100 (175->100 unused, see below)
RENUMBER = {v: v - 75 for v in range(150, 175)}    # 150..174 -> 75..99 ; 175 has nowhere to go
PLANETB_VLAN = 87
# 162..174 map onto 87..99 by the formula; 87 is PlanetB, so spares are 88..99 (= 163..174) and
# 162 and 175 simply end (twelve spares, as the plan says).
SPARE_SRC = {v: v - 75 for v in range(163, 175)}   # 163->88 ... 174->99

# Workbook status: inactive VLANs are created without a name and without a policy
# (plan v2 section 11; 48 counts as active, 57 never existed on the ATP500).
INACTIVE = {11, 12, 19, 22, 23, 25, 29, 30, 31, 33, 43, 45, 47, 61, 63, 65, 68}
UNUSED_ATP = {57}

# Management VLAN 1 (Mat, 23 Oct 2026 evening): the aggregate's untagged side replicates the ATP500's
# LAN1, 192.168.1.1/24 with the LAN_POOL scope (.33 + 200, 2 days), so every switch and AP keeps its
# address. The island's 192.168.201.0/24 is not carried over at all: SW101, SW102 and SW14 are given
# .101/.102/.114 in Nebula at the start of the x1 window (reservations below back that up if they are
# left on DHCP). Addresses and MACs: configs/switches/NOTES.md.
MGMT_IP = '192.168.1.1'
MGMT_RANGE = ('192.168.1.33', '192.168.1.232')   # LAN_POOL: starting-address .33 pool-size 200
MGMT_LEASE = 172800                              # LAN_POOL: lease 2 0 0
MGMT_RESERVATIONS = [
    ('192.168.1.33', 'bc:cf:4f:bb:d8:b3', 'SW12 PH3'),
    ('192.168.1.34', 'bc:cf:4f:bb:e4:7b', 'SW06 FH2'),
    ('192.168.1.35', 'bc:cf:4f:bb:c8:f4', 'SW04 PH2'),
    ('192.168.1.36', 'bc:cf:4f:bb:cb:55', 'SW08 CW3'),
    ('192.168.1.37', 'bc:cf:4f:ce:00:92', 'SW15 Basement'),
    ('192.168.1.38', 'bc:cf:4f:bb:e6:85', 'SW02 main comms'),
    ('192.168.1.39', 'bc:cf:4f:bb:ca:e1', 'SW01 main comms, core'),
    ('192.168.1.40', 'bc:cf:4f:bb:e6:2e', 'SW07 FH2'),
    ('192.168.1.41', 'bc:cf:4f:bb:e3:76', 'SW05 CW2'),
    ('192.168.1.42', 'bc:cf:4f:c4:bc:90', 'SW10 FH3'),
    ('192.168.1.43', 'bc:cf:4f:c4:bf:48', 'SW11 FH3'),
    ('192.168.1.44', 'bc:cf:4f:c4:bb:e2', 'SW09 FH3'),
    ('192.168.1.45', 'bc:cf:4f:bb:c4:a6', 'SW13 PH3'),
    ('192.168.1.46', 'bc:cf:4f:5a:7b:9b', 'FHG2 GS1350 (not in Nebula)'),
    ('192.168.1.47', 'bc:cf:4f:bb:ca:16', 'SW03 PH1'),
    ('192.168.1.101', '80:ea:0b:25:b1:d6', 'SW101 (was 192.168.201.2)'),
    ('192.168.1.102', '80:ea:0b:25:b1:66', 'SW102 (was 192.168.201.3)'),
    ('192.168.1.114', 'bc:cf:4f:bb:c4:6c', 'SW14 FHG (was 192.168.201.4)'),
]

# ---------------------------------------------------------------- FortiOS config parser
def parse_fortios(path):
    """Nested dict: {'system interface': {'vlan150': {...}}, 'firewall policy': {'6': {...}}}.
    Keeps only the tables we need; 'set' values are stored as raw strings (quotes kept)."""
    want = {'system interface', 'system dhcp server', 'firewall policy', 'firewall address',
            'firewall vip', 'firewall ippool', 'firewall service custom'}
    tables = {}
    stack = []       # (kind, name)
    cur = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith('config '):
                stack.append(('config', line[7:]))
                continue
            if line.startswith('edit '):
                name = line[5:].strip().strip('"')
                stack.append(('edit', name))
                if len(stack) == 2 and stack[0][1] in want:
                    cur = tables.setdefault(stack[0][1], {}).setdefault(name, {'_sub': {}})
                continue
            if line in ('next', 'end'):
                if stack:
                    stack.pop()
                if len(stack) < 2:
                    cur = None
                continue
            if cur is None:
                continue
            if line.startswith('set ') or line.startswith('unset '):
                parts = line.split(None, 2)
                key = parts[1]
                val = parts[2] if len(parts) > 2 else ''
                if len(stack) == 2:
                    cur[key] = val
                else:
                    sub = '/'.join(n for k, n in stack[2:])
                    cur['_sub'].setdefault(sub, {})[key] = val
    return tables


# ---------------------------------------------------------------- ATP500 parser
def parse_atp(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    pools, statics, vlans, bwm = {}, [], {}, {}
    for m in re.finditer(r'^ip dhcp pool (\S+)\n(.*?)^!', txt, re.M | re.S):
        name, body = m.group(1), m.group(2)
        d = dict(re.findall(r'^ (\S+) (.*)$', body, re.M))
        if 'host' in d:
            statics.append({'ip': d['host'], 'mac': d.get('hardware-address', ''),
                            'desc': d.get('description', ''), 'pool': name})
        else:
            net = d.get('network', '').split()
            sa = re.match(r'(\S+) pool-size (\d+)', d.get('starting-address', ''))
            pools[name] = {'network': net[0] if net else '', 'router': d.get('default-router', ''),
                           'start': sa.group(1) if sa else '', 'size': int(sa.group(2)) if sa else 0,
                           'lease': d.get('lease', ''),
                           'dns': [d[k] for k in ('first-dns-server', 'second-dns-server', 'third-dns-server') if k in d]}
    for m in re.finditer(r'^interface (vlan\d+)\n(.*?)^!', txt, re.M | re.S):
        name, body = m.group(1), m.group(2)
        d = {}
        for ln in body.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            k, _, v = ln.partition(' ')
            d.setdefault(k, v)
        vlans[int(name[4:])] = {
            'description': d.get('description', ''),
            'ip': d.get('ip', '').replace('address ', '').split(),
            'pool': d.get('ip dhcp-pool', '') or re.search(r'ip dhcp-pool (\S+)', body).group(1) if 'dhcp-pool' in body else '',
            'shutdown': 'shutdown' in d,
            'vlan-id': int(re.search(r'vlan-id (\d+)', body).group(1)),
        }
    for m in re.finditer(r'^bwm (\d+)\n(.*?)^!', txt, re.M | re.S):
        body = m.group(2)
        desc = re.search(r'description (.*)', body)
        inc = re.search(r'incoming-interface interface (vlan\d+)', body)
        ib = re.search(r'inbound guarantee-bandwidth (\d+)', body)
        ob = re.search(r'outbound guarantee-bandwidth (\d+)', body)
        if inc:
            bwm.setdefault(int(inc.group(1)[4:]), []).append({
                'rule': int(m.group(1)), 'desc': desc.group(1).strip() if desc else '',
                'down': int(ib.group(1)) if ib else 0, 'up': int(ob.group(1)) if ob else 0,
                'deactivated': '\n deactivate' in body})
    return pools, statics, vlans, bwm


# ---------------------------------------------------------------- helpers
def ip_add(ip, n):
    a = ip.split('.')
    return '%s.%s.%s.%d' % (a[0], a[1], a[2], int(a[3]) + n)


def octet(ip, i=3):
    return int(ip.split('.')[i])


def q(s):
    return '"%s"' % s.replace('"', "'")


def alias_of(name):
    name = re.sub(r'^[Vv][Ll][Aa][Nn]_?\d*_?', '', name).replace('_', ' ').strip()
    return name[:25].rstrip()


def client_alias(sheet_client):
    """'PH3.6-8 - Cake Architecture' -> 'Cake Architecture' (the room code stays in the description)."""
    name = re.sub(r'^[A-Z]{1,3}[0-9][0-9A-Za-z.\-/ ]*?\s+-\s+', '', sheet_client).strip()
    return name[:25].rstrip()


def zld_lease_seconds(s):
    if s.strip() == 'infinite':
        return INFINITE_LEASE_BECOMES, True
    d, h, m = (int(x) for x in s.split())
    return d * 86400 + h * 3600 + m * 60, False


def fgt_dhcp_block(idx_comment, iface, gw, start, end, lease, reservations=()):
    """FortiOS dhcp server entry. 'edit 0' lets FortiOS pick the next free id."""
    out = ['    edit 0   # %s' % idx_comment,
           '        set interface %s' % q(iface),
           '        set default-gateway %s' % gw,
           '        set netmask 255.255.255.0',
           '        set lease-time %d' % lease,
           '        set dns-service default',
           '        config ip-range',
           '            edit 1',
           '                set start-ip %s' % start,
           '                set end-ip %s' % end,
           '            next',
           '        end']
    if reservations:
        out.append('        config reserved-address')
        for i, (ip, mac, desc) in enumerate(reservations, 1):
            out += ['            edit %d' % i,
                    '                set ip %s' % ip,
                    '                set mac %s' % mac.lower(),
                    '                set action reserved',
                    '                set description %s' % q(desc),
                    '            next']
        out.append('        end')
    out.append('    next')
    return out


def fgt_iface_block(name, vid, alias, desc, out_kbps, in_kbps, dev_ident=True, role='lan'):
    out = ['    edit %s' % q(name),
           '        set vdom "root"',
           '        set type vlan',
           '        set interface %s' % q(AGG),
           '        set vlanid %d' % vid,
           '        set ip 192.168.%d.254 255.255.255.0' % vid,
           '        set allowaccess ping',
           '        set role %s' % role,
           '        set device-identification %s' % ('enable' if dev_ident else 'disable')]
    if alias:
        out.append('        set alias %s' % q(alias))
    if desc:
        out.append('        set description %s' % q(desc[:255]))
    if out_kbps:
        out.append('        set outbandwidth %d' % out_kbps)
    if in_kbps:
        out.append('        set inbandwidth %d' % in_kbps)
    out.append('    next')
    return out


def fgt_addr_block(name, vid):
    return ['    edit %s' % q('%s address' % name),
            '        set type interface-subnet',
            '        set subnet 192.168.%d.0 255.255.255.0' % vid,
            '        set interface %s' % q(name),
            '    next']


UTM_KEYS = ['utm-status', 'inspection-mode', 'profile-type', 'profile-protocol-options',
            'ssl-ssh-profile', 'av-profile', 'webfilter-profile', 'dnsfilter-profile',
            'ips-sensor', 'application-list', 'logtraffic']
UTM_DEFAULT = {   # the pattern every live FortiGate tenant policy uses today (vlan150 etc.)
    'utm-status': 'enable', 'inspection-mode': 'flow', 'profile-type': 'single',
    'profile-protocol-options': '"default"', 'ssl-ssh-profile': '"certificate-inspection"',
    'av-profile': "''", 'webfilter-profile': '"default"', 'dnsfilter-profile': '"default"',
    'ips-sensor': "''", 'application-list': '"default"', 'logtraffic': 'utm'}


def fgt_policy_block(name, srcintf, dstintf, srcaddr, dstaddr, service='"ALL"', nat=True,
                     pool=None, utm=None, comment=''):
    utm = utm or UTM_DEFAULT
    out = ['    edit 0',
           '        set name %s' % q(name),
           '        set srcintf %s' % q(srcintf),
           '        set dstintf %s' % q(dstintf),
           '        set action accept',
           '        set srcaddr %s' % srcaddr,
           '        set dstaddr %s' % dstaddr,
           '        set schedule "always"',
           '        set service %s' % service]
    if utm.get('utm-status') == 'enable':
        for k in UTM_KEYS:
            v = utm.get(k, UTM_DEFAULT.get(k))
            if v is None or v in ("''", ''):
                continue
            out.append('        set %s %s' % (k, v))
    else:
        out += ['        set utm-status disable',
                '        set ssl-ssh-profile "no-inspection"',
                '        set logtraffic %s' % utm.get('logtraffic', 'utm')]
    out.append('        set nat %s' % ('enable' if nat else 'disable'))
    if nat and pool:
        out += ['        set ippool enable', '        set poolname %s' % q(pool)]
    if comment:
        out.append('        set comments %s' % q(comment))
    out.append('    next')
    return out


def write(name, lines, header):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# %s\n# Generated by plans/gen-fortigate-cli.py from the 13/14 Oct 2026 captures. Do not edit; re-run.\n'
                '# Lines starting with # are comments for the reader; FortiOS ignores them when pasted.\n\n' % header)
        f.write('\n'.join(lines) + '\n')
    print('wrote %s (%d lines)' % (os.path.relpath(path, ROOT), len(lines)))


# ---------------------------------------------------------------- main
def main():
    fgt = parse_fortios(FGT)
    pools, statics, atp_vlans, bwm = parse_atp(ATP)
    sheet = {}
    with open(SHEET, encoding='utf-8', errors='replace', newline='') as f:
        for row in csv.reader(f):
            if len(row) >= 8 and re.match(r'^\d+\.0$', row[2] or ''):
                sheet[int(float(row[2]))] = row[7].strip()
    flags = []       # things for Mat to look at
    summary = []     # one line per VLAN

    fgt_if = fgt['system interface']
    fgt_dhcp = {v['interface'].strip('"'): (k, v) for k, v in fgt['system dhcp server'].items() if 'interface' in v}
    fgt_pol = fgt['firewall policy']
    pol_by_src = {}
    for pid, p in fgt_pol.items():
        pol_by_src.setdefault(p.get('srcintf', '').strip('"'), []).append((int(pid), p))

    # ================================================================ 10: mgmt move
    L = []
    L += ['# STEP 0, part 1: add the new management address alongside the old one. Nothing is removed.',
          '# Run from the console or over SSH to 192.168.10.99. The old address keeps working.',
          'config system interface',
          '    edit "mgmt"',
          '        set secondary-IP enable',
          '        config secondaryip',
          '            edit 1',
          '                set ip %s 255.255.255.0' % NEW_MGMT_FGT,
          '                set allowaccess ping https ssh',
          '            next',
          '        end',
          '    next',
          'end',
          '',
          '# Then on the jump box (Mat present; touches the onboard NIC, not the USB NIC or Tailscale):',
          '#   sudo nmcli con mod fortigate-mgmt +ipv4.addresses %s/24' % NEW_MGMT_JB,
          '#   sudo nmcli con up fortigate-mgmt',
          '#   ping -c3 %s ; ssh ro-jumpbox@%s "get system status"' % (NEW_MGMT_FGT, NEW_MGMT_FGT),
          '#   sudo tailscale set --advertise-routes=192.168.254.0/24,192.168.10.0/24,192.168.5.0/24',
          '#   (approve 192.168.5.0/24 in the Tailscale admin console; test from the laptop)',
          '',
          '# STEP 0, part 2: swap. FROM THE CONSOLE ONLY: this drops any SSH session on 192.168.10.99.',
          '# Only after part 1 is proven from the laptop over Tailscale.',
          'config system interface',
          '    edit "mgmt"',
          '        config secondaryip',
          '            delete 1',
          '        end',
          '        set secondary-IP disable',
          '        set ip %s 255.255.255.0' % NEW_MGMT_FGT,
          '    next',
          'end',
          '',
          '# Jump box afterwards:',
          '#   sudo nmcli con mod fortigate-mgmt ipv4.addresses %s/24' % NEW_MGMT_JB,
          '#   sudo nmcli con up fortigate-mgmt',
          '#   sudo tailscale set --advertise-routes=192.168.254.0/24,192.168.5.0/24',
          '#   edit HOST= in ~/jumpbox-setup/fortigate-cmd.sh and fortigate-discover.sh, private/jb.env, bin/jb status list',
          '# Check: bin/jb fgt "get system interface physical" shows mgmt %s and NO 192.168.10.x anywhere.' % NEW_MGMT_FGT]
    write('10-fgt-mgmt-move.txt', L, 'FortiGate management 192.168.10.99 -> %s (plan v2 step 0)' % NEW_MGMT_FGT)

    # ================================================================ 20/21: shorten leases
    L = ['# Run on the FortiGate a day or more before the renumbering (plan v2 section 9).',
         '# Clients on 150-160 then hold %d-second leases and re-address within minutes after the PVID flip.' % SHORT_LEASE,
         'config system dhcp server']
    for vid in range(150, 161):
        name = 'vlan%d' % vid
        if name in fgt_dhcp:
            L += ['    edit %s   # %s' % (fgt_dhcp[name][0], name), '        set lease-time %d' % SHORT_LEASE, '    next']
    L += ['end', '', '# Undo (after the renumbering, on the NEW vlan75-85 servers the lease is already 604800; the old servers get deleted).']
    write('20-fgt-shorten-leases.txt', L, 'FortiGate DHCP lease-time %ds on vlan150-160 (before step 3)' % SHORT_LEASE)

    L = ['# ATP500, full admin (--admin, Google Authenticator) or console. ZLD syntax: lease <days> <hours> <minutes>.',
         '# Shortens every tenant pool to 10 minutes so stale leases die quickly after each cabinet moves.',
         '# Same subnet and gateway on the FortiGate replica, so clients mostly keep working; this just tidies renewals.',
         'configure terminal']
    L += ['# LAN_POOL (the switches\' and APs\' own 192.168.1.x scope) is deliberately NOT shortened: the',
          '# FortiGate replicates that subnet on the aggregate, so management devices keep their addresses',
          '# exactly like the tenants do.']
    for vid in sorted(atp_vlans):
        p = atp_vlans[vid]['pool']
        if p and p in pools and pools[p]['lease'] != ATP_SHORT_LEASE:
            L += ['ip dhcp pool %s' % p, ' lease %s' % ATP_SHORT_LEASE, 'exit']
    L += ['write', 'exit', '', '# Undo: lease 2 0 0 on each pool (or leave; the ATP500 is retired at step 6).']
    write('21-atp500-shorten-leases.txt', L, 'ATP500 DHCP lease 10 minutes on every tenant pool (before step 4)')

    # ================================================================ 30: clear x1 and x2
    L = ['# STEP 1a: free x1 and x2 so they can join the new aggregate. PLANNED OUTAGE for PlanetB (vlan70)',
         '# and island management (192.168.201.0/24) from here until 40-fgt-build is applied. Mat at the console.',
         '# Order matters: policies, then addresses, then DHCP servers, then VLAN interfaces, then the parent.',
         '# "entry is used" from FortiOS means something above was missed; stop and look, nothing is damaged.',
         '',
         'config firewall policy']
    for pid in ('32', '33', '34'):
        L.append('    delete %s   # %s' % (pid, fgt_pol[pid]['name']))
    L += ['end', '', 'config firewall address']
    for a in ('vlan70 address', 'vlan200-TEST address', 'x1 address'):
        L.append('    delete %s' % q(a))
    L += ['end', '', 'config system dhcp server']
    for ifn in ('vlan70', 'vlan200-TEST', 'x1', 'fortilink'):
        if ifn in fgt_dhcp:
            L.append('    delete %s   # %s' % (fgt_dhcp[ifn][0], ifn))
    L += ['end', 'config system dhcp6 server', '    delete 1   # fortilink', 'end', '',
          'config system interface',
          '    delete "vlan70"',
          '    delete "vlan200-TEST"',
          '    edit "x1"',
          '        set ip 0.0.0.0 0.0.0.0',
          '        unset allowaccess',
          '        set alias \'\'',
          '        set role undefined',
          '    next',
          '    edit "fortilink"',
          '        set fortilink disable',
          '        unset member',
          '    next',
          '    delete "fortilink"   # may say "entry is used"; harmless, x2 is already free after unset member',
          '    edit "port16"   # down, but holds 192.168.1.99/24: FortiOS refuses the aggregate\'s 192.168.1.1/24 while this exists',
          '        set ip 0.0.0.0 0.0.0.0',
          '        unset allowaccess',
          '    next',
          'end',
          '',
          '# Check before building: diagnose netlink aggregate list   (x1 and x2 in no aggregate)',
          '#                        get system interface physical   (x1 no IP, x2 no IP)']
    write('30-fgt-clear-x1-x2.txt', L, 'FortiGate: clear x1 (vlan70, vlan200-TEST, 192.168.201.1) and x2 (fortilink) for the LAG (step 1a)')

    # ================================================================ 40: build
    L = ['# STEP 1b: the aggregate, island management scope, pools, VIPs, then all 90 VLAN interfaces',
         '# with their DHCP scopes. Paste in order. Policies are in 41-fgt-policies.txt.',
         '',
         '# --- aggregate --------------------------------------------------------------',
         'config system interface',
         '    edit %s' % q(AGG),
         '        set vdom "root"',
         '        set type aggregate',
         '        set member "x1" "x2"',
         '        set lacp-mode active',
         '        set lacp-speed slow',
         '        set algorithm L4',
         '        set ip %s 255.255.255.0' % MGMT_IP,
         '        set allowaccess ping',
         '        set role lan',
         '        set alias "LAN-10G"',
         '        set description "x1+x2 20G LACP to SW101 SFP1+2; untagged = mgmt VLAN 1 192.168.1.0/24 (replica of ATP500 LAN1); tenant VLANs 10-99 tagged"',
         '        set device-identification enable',
         '        set lldp-transmission enable',
         '    next',
         'end',
         '',
         '# --- management VLAN 1 DHCP: replica of the ATP500 LAN_POOL, with the known switches pinned -------',
         '# Switches and APs on the SW01 side keep their 192.168.1.x when their cabinet moves. SW101, SW102 and',
         '# SW14 are set to 192.168.1.101/.102/.114 (gateway .1) in Nebula at the start of the x1 window; the',
         '# reservations below give them the same addresses if they are ever put back on DHCP.',
         'config system dhcp server']
    L += fgt_dhcp_block('mgmt VLAN 1, copy of ATP500 LAN_POOL', AGG, MGMT_IP,
                        MGMT_RANGE[0], MGMT_RANGE[1], MGMT_LEASE, MGMT_RESERVATIONS)
    L += ['end', '',
          '# --- public addressing (decided by Mat 23 Oct 2026). Everyone NATs to the x4 address %s;' % SHARED_EGRESS,
          '# --- only the two tenants who asked get their own: .35 Thames Reach, .36 Cafe OTO. .33 ReLine dead, .34 Mediorite.',
          'config firewall ippool']
    for name, s, e in (POOL_TR, POOL_OTO):
        L += ['    edit %s' % q(name), '        set type overload', '        set startip %s' % s,
              '        set endip %s' % e, '    next']
    L += ['end', '', 'config firewall service custom',
          '    edit %s' % q(OTO_SERVICE[0]),
          '        set tcp-portrange %s' % OTO_SERVICE[1],
          '        set udp-portrange %s' % OTO_SERVICE[1],
          '        set comment "Cafe OTO inbound, per James Dunn 23 Oct 2026"',
          '    next', 'end', '',
          'config firewall vip']
    for name, ext, mapped in (VIP_TR, VIP_OTO):
        L += ['    edit %s' % q(name), '        set type static-nat', '        set extip %s' % ext,
              '        set mappedip %s' % q(mapped), '        set extintf %s' % q(WAN),
              '        set portforward disable', '    next']
    L += ['end', '']

    # ---- the VLAN set
    plan = {}   # vid -> dict(name, alias, desc, active, out, in, dhcp(start,end,lease), reservations, src, pool, utm, extra_policies)
    # ATP500 replicas 10..74 (+57 unused)
    for vid in range(10, 75):
        if vid in UNUSED_ATP:
            plan[vid] = dict(src='unused on ATP500', active=False, alias='', desc='', out=0, inb=0,
                             dhcp=('192.168.%d.2' % vid, '192.168.%d.250' % vid, 604800), res=[], pool=None, utm=None)
            continue
        a = atp_vlans[vid]
        active = vid not in INACTIVE
        pool = pools.get(a['pool'], {})
        if pool:
            start = pool['start']
            end_n = min(octet(start) + pool['size'] - 1, 253)
            end = '192.168.%d.%d' % (vid, end_n)
            lease, was_inf = zld_lease_seconds(pool['lease'])
            if was_inf:
                flags.append('VLAN %d: ATP500 lease was infinite; replica uses 7 days' % vid)
            if octet(start) + pool['size'] - 1 >= 254:
                pass  # clamped silently; the gateway is .254
        else:
            start, end, lease = '192.168.%d.10' % vid, '192.168.%d.250' % vid, 604800
            flags.append('VLAN %d: no DHCP pool on the ATP500; replica gets .10-.250 anyway' % vid)
        res = [(s['ip'], s['mac'], s['desc']) for s in statics
               if octet(s['ip'], 2) == vid and not s['mac'].startswith('00:00:00')]
        rules = [r for r in bwm.get(vid, []) if not r['deactivated']]
        out_k = in_k = 0
        if rules:
            r = rules[0]
            out_k, in_k = r['down'], r['up']
            if len(rules) > 1:
                flags.append('VLAN %d: %d BWM rules on the ATP500 (%s); used rule %d %s' % (
                    vid, len(rules), ', '.join('%d %s' % (x['rule'], x['desc']) for x in rules), r['rule'], r['desc']))
        desc = a['description']
        plan[vid] = dict(src='ATP500 %s' % ('vlan%d' % vid), active=active,
                         alias=alias_of(desc) if active else '', desc=desc if active else '',
                         out=out_k, inb=in_k, dhcp=(start, end, lease), res=res,
                         pool=None, utm=None)
    # VLAN 72 / 73: both ATP500 rules sit on vlan73 (Ashford's rule names 72). Carry them to the right VLANs.
    r73 = {r['desc']: r for r in bwm.get(73, [])}
    if 'Vlan72_AshfordSons' in r73 and 'Vlan73_MAKE' in r73:
        plan[72]['out'], plan[72]['inb'] = r73['Vlan72_AshfordSons']['down'], r73['Vlan72_AshfordSons']['up']
        plan[73]['out'], plan[73]['inb'] = r73['Vlan73_MAKE']['down'], r73['Vlan73_MAKE']['up']
        flags.append('VLAN 72/73: ATP500 rule "Vlan72_AshfordSons" was attached to vlan73; replica puts 100M on 72 and 30M on 73 (Mat to confirm)')
    if plan[13]['out'] == 40000:
        flags.append('VLAN 13: carries the ATP500 cap 40000/10000 kbps (therapy block complaint, notes/therapy-block-ap-2026-10-23.md); change to 61440 if Mat approves the raise')
    plan[54]['pool'] = POOL_TR[0]
    plan[71]['pool'] = POOL_OTO[0]
    if MEDIORITE_ON_58:
        plan[58]['desc'] = (plan[58]['desc'] + ' (public IP 193.221.131.34 via VIP)').strip()

    # FortiGate renumbered 150..160 -> 75..85, 161 -> 86
    for old in range(150, 162):
        new = RENUMBER[old]
        name_old = 'vlan%d' % old
        i = fgt_if.get(name_old, {})
        out_k = int(i.get('outbandwidth', '0') or 0)
        in_k = int(i.get('inbandwidth', '0') or 0)
        client = sheet.get(old, '')
        active = old not in (155, 161) or (old == 161 and not MEDIORITE_ON_58)
        if old == 155:
            client = ''
        if old == 161 and MEDIORITE_ON_58:
            client = ''
        d = fgt_dhcp.get(name_old)
        if d:
            rng = d[1]['_sub'].get('ip-range/1', {})
            dhcp = (rng.get('start-ip', '192.168.%d.10' % old).replace('.%d.' % old, '.%d.' % new),
                    rng.get('end-ip', '192.168.%d.250' % old).replace('.%d.' % old, '.%d.' % new),
                    int(d[1].get('lease-time', '604800')))
        else:
            dhcp = ('192.168.%d.2' % new, '192.168.%d.250' % new, 604800)
        # policy pattern: the general outbound policy for this VLAN, plus any extra (whitelist) ones
        pols = sorted(pol_by_src.get(name_old, []))
        general = [p for pid, p in pols if p.get('dstaddr') == '"all"' and p.get('dstintf') == '"x4"']
        extras = [(pid, p) for pid, p in pols if not (p.get('dstaddr') == '"all"' and p.get('dstintf') == '"x4"')]
        utm = {k: general[0][k] for k in UTM_KEYS if k in general[0]} if general else None
        plan[new] = dict(src='FortiGate %s' % name_old, active=active, alias=client_alias(client) if active else '',
                         desc=client if active else '', out=out_k, inb=in_k, dhcp=dhcp, res=[],
                         pool=None, utm=utm, extras=extras, old=old)
    # PlanetB 87 (today FortiGate vlan70 on x1)
    i70 = fgt_if.get('vlan70', {})
    d70 = fgt_dhcp.get('vlan70')
    plan[PLANETB_VLAN] = dict(src='FortiGate vlan70 (x1), PlanetB via SW14', active=True, alias='PlanetB',
                              desc='PlanetB, FHG via SW14 (was FortiGate vlan70 on x1, alias LeadersUnlocked)',
                              out=int(i70.get('outbandwidth', '0') or 0), inb=int(i70.get('inbandwidth', '0') or 0),
                              dhcp=('192.168.87.2', '192.168.87.253', int(d70[1].get('lease-time', '604800')) if d70 else 604800),
                              res=[], pool=None,
                              utm={k: fgt_pol['32'][k] for k in UTM_KEYS if k in fgt_pol['32']}, extras=[], old=70)
    # spares 88..99 (from 163..174)
    for old, new in SPARE_SRC.items():
        plan[new] = dict(src='spare (was FortiGate vlan%d)' % old, active=False, alias='', desc='', out=0, inb=0,
                         dhcp=('192.168.%d.2' % new, '192.168.%d.250' % new, 604800), res=[], pool=None, utm=None)

    assert sorted(plan) == list(range(10, 100)), sorted(set(range(10, 100)) ^ set(plan))

    # ---- interfaces
    L += ['# --- VLAN interfaces 10-99 (name only where a tenant is active) --------------------',
          'config system interface']
    for vid in range(10, 100):
        p = plan[vid]
        L += ['    # vlan%d  %s%s' % (vid, p['src'], '' if p['active'] else '  (inactive/spare: no name, no policy)')]
        L += fgt_iface_block('vlan%d' % vid, vid, p['alias'], p['desc'], p['out'], p['inb'])
    L += ['end', '']
    # ---- addresses (only for VLANs that get a policy)
    L += ['# --- address objects for the VLANs that get a policy --------------------------------',
          'config firewall address',
          '    edit %s' % q('%s address' % AGG),
          '        set type interface-subnet',
          '        set subnet 192.168.1.0 255.255.255.0',
          '        set interface %s' % q(AGG),
          '    next']
    for vid in range(10, 100):
        if plan[vid]['active']:
            L += fgt_addr_block('vlan%d' % vid, vid)
    L += ['end', '']
    # ---- DHCP
    L += ['# --- DHCP scopes (range, lease, reservations from the device that serves the VLAN today) --',
          'config system dhcp server']
    for vid in range(10, 100):
        p = plan[vid]
        s, e, lease = p['dhcp']
        L += fgt_dhcp_block('vlan%d  %s' % (vid, p['src']), 'vlan%d' % vid, '192.168.%d.254' % vid, s, e, lease, p['res'])
    L += ['end', '',
          '# Check: get system interface | grep -c "LAN-Bond-10G"   (expect 90)',
          '#        diagnose netlink aggregate name %s          (x1, x2 both up once SW101 ports 1+2 are patched)' % AGG,
          '#        execute ping 192.168.1.101 / .102 / .114     (SW101, SW102, SW14 on their new addresses)',
          '#        execute dhcp lease-list vlan87               (PlanetB back, once SW14 PVIDs are 87)']
    write('40-fgt-build-lan-bond-10g.txt', L, 'FortiGate: aggregate %s, island DHCP, pools, VIPs, 90 VLAN interfaces + DHCP (step 1b)' % AGG)

    # ================================================================ 41: policies
    L = ['# STEP 1c: firewall policies. One accept+NAT to %s per active VLAN, mirroring the live pattern.' % WAN,
         '# Everyone egresses as %s (plain NAT to the x4 address, no pool); only vlan54 and vlan71 use a pool.' % SHARED_EGRESS,
         '# Whitelist/exception policies are created BEFORE the general policy of the same VLAN so they match first.',
         '# All ids are "edit 0" (FortiOS assigns). Inactive and spare VLANs get no policy at all.',
         '',
         'config firewall policy',
         '    # Island management first: SW101, SW102, SW14 and every re-patched cabinet switch reach Nebula',
         '    # through this (it replaces policy 34 "Interface LAN x1", deleted in 30-fgt-clear-x1-x2.txt).']
    L += fgt_policy_block('LAN-10G mgmt -> internet', AGG, WAN, q('%s address' % AGG), '"all"', '"ALL"', nat=True,
                          pool=None, utm={k: fgt_pol['34'][k] for k in UTM_KEYS if k in fgt_pol['34']},
                          comment='switch and AP management VLAN 1, 192.168.1.0/24; was policy 34 on x1')
    for vid in range(10, 100):
        p = plan[vid]
        if not p['active']:
            continue
        name = 'vlan%d' % vid
        for pid, x in p.get('extras', []):
            # e.g. vlan152 -> *.ecare123.site HTTP/HTTPS, utm off. Keep everything except the interface and source.
            if x.get('dstintf') != '"x4"':
                flags.append('VLAN %d: old policy %d (%s) is not an outbound-to-x4 policy; not copied' % (vid, pid, x.get('name')))
                continue
            if x.get('dstaddr') == '"Dupe-FW"':
                continue   # CoLab relic
            utm = {k: x[k] for k in UTM_KEYS if k in x}
            L += ['    # copied from policy %d %s' % (pid, x.get('name'))]
            L += fgt_policy_block('%s-%s' % (name, x.get('name', '').strip('"').split('-', 1)[-1]), name, WAN,
                                  q('%s address' % name), x.get('dstaddr', '"all"'), x.get('service', '"ALL"'),
                                  nat=x.get('nat', 'enable') == 'enable', pool=None, utm=utm,
                                  comment='was %s (policy %d)' % (x.get('name', '').strip('"'), pid))
        L += fgt_policy_block(name, name, WAN, q('%s address' % name), '"all"', '"ALL"', nat=True,
                              pool=p['pool'], utm=p['utm'],
                              comment=('%s; %s' % (p['alias'], p['src']))[:255])
    # inbound VIP policies (nat disabled so the tenant sees real source addresses)
    L += ['', '    # --- inbound to the two carried-over public IPs ---',
          '    # Thames Reach: everything to 193.221.131.35 -> 192.168.54.253 (as the ATP500 1:1 did)']
    L += fgt_policy_block('internet -> ThamesReach .35', WAN, 'vlan54', '"all"', q(VIP_TR[0]), '"ALL"', nat=False,
                          utm={'utm-status': 'disable', 'logtraffic': 'utm'}, comment='carried from ATP500 VLAN54_THAMES')
    L += ['    # Cafe OTO: TCP/UDP %s to 193.221.131.36 -> 192.168.71.1 (James Dunn, 23 Oct 2026)' % OTO_SERVICE[1]]
    L += fgt_policy_block('internet -> CafeOTO .36', WAN, 'vlan71', '"all"', q(VIP_OTO[0]), q(OTO_SERVICE[0]), nat=False,
                          utm={'utm-status': 'disable', 'logtraffic': 'utm'}, comment='carried from ATP500 Vlan71_CafeOTO, fresh build')
    L += ['end', '',
          '# Check: show firewall policy | grep -c "set srcintf \\"vlan"   and a test host on SW101 in a replicated VLAN:',
          '#   gets a lease, reaches the internet, curl ifconfig.me shows %s, cannot ping its ATP500 twin.' % SHARED_EGRESS]
    write('41-fgt-policies.txt', L, 'FortiGate: policies for the active VLANs on %s, inbound VIP policies (step 1c)' % AGG)

    # ================================================================ 50: Mediorite VIP
    L = []
    if MEDIORITE_ON_58:
        L += ['# Apply when PH1 (SW03) is re-patched: Mediorite (VLAN 58, 192.168.58.3) is then behind the FortiGate.',
              '# Their public IP becomes 193.221.131.34, the VIP Asim prepared for vlan161; 161/86 is not used.',
              'config firewall vip',
              '    edit "VIP-193.221.131.34"',
              '        set mappedip %s' % q(MEDIORITE_HOST_58),
              '    next',
              'end',
              'config firewall policy',
              '    edit 17   # internet -> Vlan161',
              '        set name "internet -> Mediorite .34"',
              '        set dstintf "vlan58"',
              '        set nat disable',
              '    next',
              'end',
              '# Outbound: vlan58 egresses via the shared pool unless Mediorite need to be SEEN as .34 outbound too.',
              '# If they do (NinjaOne allow-lists), add an overload pool 193.221.131.34-.34 and set it on policy "vlan58".',
              '# Also: SW03 port 7 stays PVID 58; the tagged 161 on it can go when vlan161 is deleted (60-...).']
    else:
        L += ['# MEDIORITE_ON_58 is False: Mediorite moves to VLAN 86 (ex-161). SW03 port 7 PVID 58 -> 86,',
              '# their device re-addressed to %s (or made DHCP with a reservation).' % MEDIORITE_HOST_86,
              'config firewall vip', '    edit "VIP-193.221.131.34"', '        set mappedip %s' % q(MEDIORITE_HOST_86), '    next', 'end',
              'config firewall policy', '    edit 17', '        set name "internet -> Mediorite .34"', '        set dstintf "vlan86"', '        set nat disable', '    next', 'end']
    write('50-fgt-mediorite-vip.txt', L, 'FortiGate: repoint Mediorite VIP 193.221.131.34 (at the PH1 cutover)')

    # ================================================================ 60: retire 150-175 etc.
    L = ['# STEP 3 tail: only after EVERY FortiGate tenant is confirmed on its new VLAN (75-85, 87) and the',
         '# SW01 T1 bond no longer carries live traffic for 150-175. Same dependency order as 30-...',
         '# Keep the old vlan15x interfaces until the last client has renewed (10-minute leases by then).',
         '',
         'config firewall policy']
    for pid, p in sorted(fgt_pol.items(), key=lambda kv: int(kv[0])):
        src = p.get('srcintf', '').strip('"')
        dst = p.get('dstintf', '').strip('"')
        if re.match(r'^vlan1[5-7]\d$', src) or re.match(r'^vlan1[5-7]\d$', dst) and not (MEDIORITE_ON_58 and pid == '17'):
            if pid == '17' and MEDIORITE_ON_58:
                continue
            L.append('    delete %s   # %s' % (pid, p.get('name')))
    L += ['end', '', 'config firewall vip', '    delete "VIP-193.221.131.33-disabled"   # ReLine, never used (Mat, 23 Oct 2026)', 'end', '',
          'config firewall address']
    for vid in list(range(150, 176)):
        if ('vlan%d address' % vid) in fgt['firewall address']:
            L.append('    delete %s' % q('vlan%d address' % vid))
    L += ['    delete "Dupe-FW"   # CoLab whitelist target, CoLab gone', 'end', '', 'config system dhcp server']
    for vid in range(150, 176):
        n = 'vlan%d' % vid
        if n in fgt_dhcp:
            L.append('    delete %s   # %s' % (fgt_dhcp[n][0], n))
    L += ['end', '', 'config system interface']
    for vid in range(150, 176):
        L.append('    delete "vlan%d"' % vid)
    L += ['end', '',
          '# Relics on port1 (vlan101 192.168.101.254 with SSL-VPN policy 2, "102"): Mat said delete (23 Oct 2026).',
          '# Separate paste so a mistake here cannot touch the tenant work above:',
          'config firewall policy', '    delete 1   # vlan101', '    delete 2   # sslvpn -> vlan101', 'end',
          'config system dhcp server']
    for n in ('vlan101', '102'):
        if n in fgt_dhcp:
            L.append('    delete %s   # %s' % (fgt_dhcp[n][0], n))
    L += ['end', 'config firewall address', '    delete "vlan101 address"', 'end',
          'config system interface', '    delete "vlan101"', '    delete "102"', 'end']
    write('60-fgt-retire-vlan150-175.txt', L, 'FortiGate: delete the old 150-175 tenant VLANs from LAN-Bond-2 (after step 3)')

    # ================================================================ 70: final
    L = ['# STEP 6: only when the ATP500 is powered off and nothing is plugged into SW01 port 2.',
         'config system interface',
         '    delete "LAN-Bond-2"   # frees port3 and port4; fails with "entry is used" if a vlan15x is still on it',
         'end',
         '# Then in Nebula: remove trunk group T1 (SW01 ports 9+10); SW102 port 12 (Cat6 already pulled) joins the',
         '# SW101/SW102 LAG on ports 11+12.']
    write('70-fgt-final-cleanup.txt', L, 'FortiGate: retire LAN-Bond-2 (step 6)')

    # ================================================================ summary + flags
    S = ['VLAN  active  alias                      down/up kbps    DHCP range                     lease   res  pool              source',
         '----  ------  -------------------------  --------------  -----------------------------  ------  ---  ----------------  ------']
    for vid in range(10, 100):
        p = plan[vid]
        s, e, lease = p['dhcp']
        S.append('%-4d  %-6s  %-25s  %6d/%-7d  %-29s  %6d  %3d  %-16s  %s' % (
            vid, 'yes' if p['active'] else '-', p['alias'], p['out'], p['inb'], '%s - %s' % (s, e), lease,
            len(p['res']), p['pool'] or (SHARED_EGRESS if p['active'] else '-'), p['src']))
    S += ['', 'Reservations carried:']
    for vid in range(10, 100):
        for ip, mac, desc in plan[vid]['res']:
            S.append('  vlan%d  %s  %s  %s' % (vid, ip, mac, desc))
    S += ['', 'Things to look at before pasting:'] + ['  - ' + f for f in flags]
    S += ['', 'Management VLAN 1 on the aggregate: %s/24 (replica of ATP500 LAN1), DHCP %s-%s lease %d, %d reservations;'
          % (MGMT_IP, MGMT_RANGE[0], MGMT_RANGE[1], MGMT_LEASE, len(MGMT_RESERVATIONS)),
          '  192.168.201.0/24 is gone; SW101/SW102/SW14 become 192.168.1.101/.102/.114 (set in Nebula at the start of the x1 window).']
    S += ['', 'Public addresses (decided by Mat 23 Oct 2026, quoted in the tenant letters):',
          '  %s  everyone, plain NAT to the x4 address (ATP500 arrivals join the FortiGate tenants and PlanetB here)' % SHARED_EGRESS,
          '  %s  Thames Reach: pool %s + VIP -> %s' % (POOL_TR[1], POOL_TR[0], VIP_TR[2]),
          '  %s  Cafe OTO: pool %s + VIP -> %s (TCP/UDP %s inbound)' % (POOL_OTO[1], POOL_OTO[0], VIP_OTO[2], OTO_SERVICE[1]),
          '  193.221.131.34  Mediorite: existing VIP, repointed to %s' % (MEDIORITE_HOST_58 if MEDIORITE_ON_58 else MEDIORITE_HOST_86),
          '  193.221.131.33  ReLine: deleted at lockdown; .37 to .62 of the /27 stay free']
    write('summary.txt', S, 'Review table: what each VLAN becomes')
    print('\n'.join('FLAG ' + f for f in flags))


if __name__ == '__main__':
    sys.exit(main())
