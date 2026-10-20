#!/usr/bin/env python3
"""Cross-reference Bootstrap's 'VLANs and Configurations' workbook against device captures."""
import csv, re, sys, os, collections, datetime

SHEETS = sys.argv[1]        # dir with csv exports of the Oct 2026 workbook
CFG = sys.argv[2]           # /srv/configs
OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)

# ---------- switch fabric ----------
SW_IP = {'SW01':'192.168.1.39','SW02':'192.168.1.38','SW03':'192.168.1.47','SW04':'192.168.1.35',
         'SW05':'192.168.1.41','SW06':'192.168.1.34','SW07':'192.168.1.40','SW08':'192.168.1.36',
         'SW09':'192.168.1.44','SW10':'192.168.1.42','SW11':'192.168.1.43','SW12':'192.168.1.33',
         'SW13':'192.168.1.45','SW15':'192.168.1.37'}
NOT_READ = {'SW14':'FortiGate x1 island 192.168.201.4, unreachable', 'SW16':'GS1350 192.168.46.4, login refused',
            'SW17':'Roof bar, separate internet', 'SW18':'offline in Nebula'}

def expand(rng):
    out=set()
    rng=rng.strip().strip('"')
    if not rng: return out
    for part in rng.split(','):
        if '-' in part:
            a,b=part.split('-'); out.update(range(int(a),int(b)+1))
        else: out.add(int(part))
    return out

sw_untag = {}   # sw -> port -> vlan
sw_tag = {}     # sw -> port -> set(vlans)
sw_vlans = {}   # sw -> set(vlans defined)
for sw,ip in SW_IP.items():
    path=f'{CFG}/switches/raw/{ip}-show-running-config-2026-10-14.txt'
    untag=collections.defaultdict(lambda:1); tag=collections.defaultdict(set); vl=set()
    v=None
    for line in open(path, errors='replace'):
        m=re.match(r'^vlan (\d+)', line)
        if m: v=int(m.group(1)); vl.add(v); fixed=set(); continue
        if v is None: continue
        if re.match(r'^\s*fixed ', line): fixed=expand(line.split(None,1)[1])
        elif re.match(r'^\s*untagged ', line):
            u=expand(line.split(None,1)[1]) if len(line.split(None,1))>1 else set()
            for p in u: untag[p]=v
            for p in fixed-u: tag[p].add(v)
            v=None
    sw_untag[sw]=dict(untag); sw_tag[sw]=dict(tag); sw_vlans[sw]=vl

# ---------- ATP500 ----------
atp_if={}
cur=None
for line in open(f'{CFG}/atp500/running-config-2026-10-13.conf', errors='replace'):
    m=re.match(r'^interface (vlan\d+)', line)
    if m: cur=m.group(1); atp_if[cur]={'desc':'','ip':''}; continue
    if cur:
        if line.startswith('!'): cur=None; continue
        m=re.match(r'^\s*description (.*)', line)
        if m: atp_if[cur]['desc']=m.group(1).strip()
        m=re.match(r'^\s*ip address (\S+) (\S+)', line)
        if m: atp_if[cur]['ip']=m.group(1)
atp_up=set(re.findall(r'^\d+\s+(vlan\d+)\s+Up', open(f'{CFG}/atp500/interface-all-2026-10-14.txt').read(), re.M))
dhcp=collections.Counter(re.findall(r'\b(vlan\d+)\b', open(f'{CFG}/atp500/dhcp-binding-2026-10-14.txt').read()))
arp=collections.Counter(re.findall(r'\b(vlan\d+)\b', open(f'{CFG}/atp500/arp-table-2026-10-14.txt').read()))
bwm={}; pr={}; vs=[]
txt=open(f'{CFG}/atp500/running-config-2026-10-13.conf', errors='replace').read()
for blk in re.findall(r'^bwm \d+\n(.*?)^!', txt, re.M|re.S):
    d=re.search(r'description (.*)', blk); i=re.search(r'incoming-interface interface (vlan\d+)', blk)
    ib=re.search(r'inbound guarantee-bandwidth (\d+)', blk); ob=re.search(r'outbound guarantee-bandwidth (\d+)', blk)
    if i: bwm.setdefault(i.group(1), []).append(f"{d.group(1).strip() if d else ''} down={int(ib.group(1))//1024 if ib else '?'}M up={int(ob.group(1))//1024 if ob else '?'}M")
for blk in re.findall(r'^policy \d+\n(.*?)^!', txt, re.M|re.S):
    i=re.search(r'^ interface (vlan\d+)', blk, re.M); s=re.search(r'snat pool (\S+)', blk)
    if i and s: pr[i.group(1)]=s.group(1)
for line in re.findall(r'^ip virtual-server .*', txt, re.M):
    vs.append(line)
addr={m.group(1):m.group(2) for m in re.finditer(r'^address-object (\S+) (\d+\.\d+\.\d+\.\d+)$', txt, re.M)}

# ---------- FortiGate ----------
fg_if={}
ftxt=open(f'{CFG}/fortigate/full-config-2026-10-13.conf', errors='replace').read()
sec=re.search(r'^config system interface\n(.*?)^end', ftxt, re.M|re.S).group(1)
for m in re.finditer(r'^    edit "([^"]+)"\n(.*?)^    next', sec, re.M|re.S):
    name,body=m.group(1),m.group(2)
    vid=re.search(r'set vlanid (\d+)', body)
    if not vid: continue
    ip=re.search(r'set ip (\S+) ', body); par=re.search(r'set interface "([^"]+)"', body)
    al=re.search(r'set alias "([^"]+)"', body); ob=re.search(r'set outbandwidth (\d+)', body); ib=re.search(r'set inbandwidth (\d+)', body)
    fg_if[int(vid.group(1))]={'name':name,'ip':ip.group(1) if ip else '','parent':par.group(1) if par else '',
        'alias':al.group(1) if al else '', 'out':int(ob.group(1))//1024 if ob else 0, 'in':int(ib.group(1))//1024 if ib else 0}
fg_arp=collections.Counter(re.findall(r'\b(vlan\d+)\b', open(f'{CFG}/fortigate/arp-2026-10-14.txt').read()))
psec=re.search(r'^config firewall policy\n(.*?)^end', ftxt, re.M|re.S).group(1)
fg_pol=collections.defaultdict(list)
for m in re.finditer(r'^    edit (\d+)\n(.*?)^    next', psec, re.M|re.S):
    body=m.group(2); n=re.search(r'set name "([^"]*)"', body); s=re.search(r'set srcintf "([^"]+)"', body); d=re.search(r'set dstintf "([^"]+)"', body)
    st='DISABLED' if 'set status disable' in body else ''
    if s: fg_pol[s.group(1)].append(f"#{m.group(1)} {n.group(1) if n else ''}->{d.group(1) if d else ''} {st}".strip())
    if d: fg_pol[d.group(1)].append(f"#{m.group(1)} {n.group(1) if n else ''} {s.group(1) if s else ''}-> {st}".strip())

# ---------- sheets ----------
def rows(name):
    with open(f'{SHEETS}/{name}.csv', newline='') as f: return list(csv.reader(f))
def vnum(s):
    m=re.search(r'(\d+)', s or ''); return int(m.group(1)) if m else None

atp_sheet={}
for r in rows('VLANs_-_ATP500')[1:]:
    if len(r)<4 or not r[2].lower().startswith('vlan'): continue
    v=vnum(r[2]); atp_sheet[v]={'status':r[1],'name':r[3],'bw':r[7] if len(r)>7 else '','pub':r[8] if len(r)>8 else '','notes':r[9] if len(r)>9 else ''}
fg_sheet={}
for r in rows('VLANS_-_FORTIGATE'):
    if len(r)>3 and re.match(r'^\d+(\.0)?$', r[2] or '') and r[3].upper().startswith('VLAN'):
        v=int(float(r[2])); fg_sheet[v]={'status':r[1],'bw':r[6] if len(r)>6 else '','client':r[7] if len(r)>7 else '','notes':' '.join(x for x in r[8:] if x)}
cfg_rows=rows('BS_config_sheet')
hdr=cfg_rows[0]
cfg=[]
for r in cfg_rows[1:]:
    r=r+['']*(13-len(r))
    cfg.append({'num':r[0],'org':r[1],'bldg':r[2],'room':r[3],'speed':r[4],'sw':r[5],'port':r[6],'roomport':r[7],'vlan':r[8],'ticket':r[9],'ipinfo':r[10],'details':' '.join(x for x in r[11:] if x)})

# ---------- port parsing ----------
DATE_RE=re.compile(r'^(\d{4})-(\d{2})-(\d{2}) 00:00:00$')
def parse_ports(s):
    s=(s or '').strip()
    if not s: return [], 'blank'
    m=DATE_RE.match(s)
    if m:
        d,mo=int(m.group(3)),int(m.group(2))
        return sorted({d,mo}), f'date-mangled "{s}" (was probably {d}/{mo})'
    if 'Switch Port' in s:   # Thames Reach free text
        nums=[int(x) for x in re.findall(r'Port (\d+)', s)] + [int(x) for x in re.findall(r'(?<![\d.])(\d{1,2})(?=,|\s|$)', s.split('Switch Port 11')[-1])] if 'Switch Port 11' in s else []
        nums=sorted({int(x) for x in re.findall(r'Port (\d+)', s)} | {11,15,16,18,19,20,21,22,23})
        return nums, 'free text'
    nums=[int(x) for x in re.findall(r'\d+', s.split('(')[0] if '(' in s and 'AP' in s else s)]
    nums=[int(x) for x in re.findall(r'\d+', s)]
    nums=[n for n in nums if 1<=n<=28]
    return sorted(set(nums)), ''
def parse_sw(s):
    m=re.search(r'SW\s?0?(\d+)', s or '')
    return f'SW{int(m.group(1)):02d}' if m else None

# ---------- port check ----------
pc=[]
for row in cfg:
    sw=parse_sw(row['sw']); ports,note=parse_ports(row['port']); vl=[int(x) for x in re.findall(r'\d+', row['vlan'])]
    claimed=vl
    if not sw:
        pc.append((row,sw,ports,claimed,'NO-SWITCH',note,'')); continue
    if sw not in SW_IP:
        pc.append((row,sw,ports,claimed,'SWITCH-NOT-READ',note,NOT_READ.get(sw,''))); continue
    if not ports:
        pc.append((row,sw,ports,claimed,'PORT-UNKNOWN',note,'')); continue
    actual=[]; ok=True; anyok=False
    for p in ports:
        u=sw_untag[sw].get(p,1); t=sorted(sw_tag[sw].get(p,set()))
        actual.append(f"p{p}=untag{u}"+(f"+tag{','.join(map(str,t))}" if t and len(t)<=6 else ('+trunk' if t else '')))
        if claimed and u in claimed: anyok=True
        elif claimed: ok=False
    if not claimed: verdict='NO-VLAN-CLAIMED'
    elif ok: verdict='OK'
    elif anyok: verdict='PARTIAL'
    else: verdict='MISMATCH'
    pc.append((row,sw,ports,claimed,verdict,note,' '.join(actual)))

with open(f'{OUT}/port-check.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['sheet_row_num','organisation','building','room','switch','ports_claimed','vlan_claimed','verdict','actual_on_switch','parse_note','sheet_details'])
    for row,sw,ports,cl,v,note,act in pc:
        w.writerow([row['num'],row['org'],row['bldg'],row['room'],sw or row['sw'],'/'.join(map(str,ports)),'/'.join(map(str,cl)),v,act,note,(row['ipinfo']+' '+row['details']).strip()])

# reverse: access ports with a tenant VLAN untagged that no sheet row claims
claimed_ports=collections.defaultdict(set)
for row,sw,ports,cl,v,note,act in pc:
    if sw in SW_IP:
        for p in ports: claimed_ports[sw].add(p)
undoc=[]
for sw in SW_IP:
    for p,u in sorted(sw_untag[sw].items()):
        if u==1: continue
        if p in claimed_ports[sw]: continue
        tags=sw_tag[sw].get(p,set())
        if len(tags)>5: continue   # trunk/uplink
        undoc.append((sw,p,u,sorted(tags)))

# ---------- VLAN register ----------
cfg_by_vlan=collections.defaultdict(list)
for row in cfg:
    for v in {int(x) for x in re.findall(r'\d+', row['vlan'])}:
        cfg_by_vlan[v].append(f"{row['org']} [{row['room']}] {parse_sw(row['sw']) or ''}:{row['port']}".strip())
sw_by_vlan=collections.defaultdict(list)
for sw in SW_IP:
    for p,u in sorted(sw_untag[sw].items()):
        if u!=1 and len(sw_tag[sw].get(p,set()))<=5: sw_by_vlan[u].append(f'{sw}:p{p}')

all_v=sorted(set(atp_sheet)|set(fg_sheet)|{int(k[4:]) for k in atp_if}|set(fg_if)|set(cfg_by_vlan)|set(sw_by_vlan)|{int(k[4:]) for k in dhcp}|{int(k[4:]) for k in fg_arp})
reg=[]
for v in all_v:
    k=f'vlan{v}'
    side = 'ATP500' if k in atp_if else ('FortiGate' if v in fg_if else '-')
    if k in atp_if and v in fg_if: side='BOTH'
    sh = atp_sheet.get(v) or fg_sheet.get(v)
    sheet_status = sh['status'] if sh else ''
    sheet_name = (atp_sheet[v]['name'] if v in atp_sheet else (fg_sheet[v]['client'] if v in fg_sheet else ''))
    sheet_bw = sh['bw'] if sh else ''
    sheet_notes = (sh.get('notes') or '') if sh else ''
    sheet_pub = atp_sheet[v]['pub'] if v in atp_sheet else ''
    dev_desc = atp_if[k]['desc'] if k in atp_if else (fg_if[v]['alias'] or fg_if[v]['name'] if v in fg_if else '')
    dev_ip = atp_if[k]['ip'] if k in atp_if else (fg_if[v]['ip'] if v in fg_if else '')
    up = ('up' if k in atp_up else 'DOWN') if k in atp_if else ('cfg' if v in fg_if else '')
    if side=='BOTH': side='ATP500'  # treat as ATP500 for the remaining columns
    leases = dhcp.get(k,0) if k in atp_if else ''
    arps = arp.get(k,0) if k in atp_if else fg_arp.get(k,0)
    bw_dev = '; '.join(bwm.get(k,[])) if k in atp_if else (f"out={fg_if[v]['out']}M in={fg_if[v]['in']}M" if v in fg_if and (fg_if[v]['out'] or fg_if[v]['in']) else '')
    snat = addr.get(pr.get(k,''),'') if k in atp_if else ''
    pol = '; '.join(fg_pol.get(k,[])) if v in fg_if else ''
    ports = ', '.join(sw_by_vlan.get(v,[]))
    tenants = ' | '.join(cfg_by_vlan.get(v,[]))
    # verdict
    live = (isinstance(arps,int) and arps>0) or (isinstance(leases,int) and leases>0)
    flags=[]
    st=sheet_status.lower()
    if side=='-' : flags.append('NOT ON EITHER GATEWAY')
    if side=='BOTH': flags.append(f"DEFINED ON BOTH GATEWAYS: ATP500 {atp_if[k]['ip']} and FortiGate {fg_if[v]['name']} on {fg_if[v]['parent']} {fg_if[v]['ip']} (FortiGate arp={fg_arp.get(k,0)})")
    if sh is None and side!='-': flags.append('NOT IN VLAN SHEET')
    if side=='ATP500' and v not in atp_sheet and v in fg_sheet: flags.append('sheet puts it on FortiGate')
    if 'inactive' in st and live: flags.append(f'SHEET INACTIVE BUT LIVE ({arps} arp/{leases} leases)')
    if 'inactive' in st and ports: flags.append('SHEET INACTIVE BUT SWITCH PORTS STILL ASSIGNED')
    if st=='active' and not live and side=='ATP500': flags.append('SHEET ACTIVE, NO HOSTS SEEN')
    if st=='active' and not live and side=='FortiGate' and v in fg_if: flags.append('SHEET ACTIVE, NO ARP ON FORTIGATE')
    if side=='FortiGate' and v in fg_if and fg_if[v]['ip']=='' : flags.append('FortiGate interface has NO IP')
    if sheet_pub and not snat and side=='ATP500': flags.append(f'sheet public IP {sheet_pub} but no policy-route SNAT')
    if snat and not sheet_pub and v in atp_sheet: flags.append(f'device SNATs to {snat}, sheet public IP column blank')
    if not ports and side!='-' and st=='active' and v not in (10,) : flags.append('no access port found on the 14 read switches')
    reg.append([v,side,sheet_status,sheet_name,sheet_bw,sheet_pub,sheet_notes,dev_desc,dev_ip,up,leases,arps,bw_dev,snat,pol,ports,tenants,'; '.join(flags)])

with open(f'{OUT}/vlan-register.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['vlan','gateway','sheet_status','sheet_name_or_client','sheet_bandwidth_mbps','sheet_public_ip','sheet_notes','device_description','device_gateway_ip','device_state','atp500_dhcp_leases','arp_entries_14oct','device_bandwidth_rule','atp500_snat_public_ip','fortigate_policies','switch_access_ports','config_sheet_tenants','flags'])
    w.writerows(reg)

# ---------- public IP register ----------
pubs={}
for name,ip in addr.items():
    if ip.startswith('157.231.128.'): pubs[ip]={'obj':name,'policy_route':[],'virtual_server':[]}
for vl,obj in pr.items():
    if obj in addr: pubs[addr[obj]]['policy_route'].append(vl)
for line in vs:
    m=re.search(r'virtual-server (\S+) interface (\S+) .*original-ip (\S+) map-to (\S+)', line)
    if m and m.group(3) in addr:
        pubs[addr[m.group(3)]]['virtual_server'].append(f"{m.group(1)}->{m.group(4)}{' DEACTIVATED' if 'deactivate' in line else ''}")
sheet_pub={}
for r in rows('Routing-Public_IP'):
    m=[x for x in r if x.startswith('Public_IP_')]
    if m:
        who=' '.join(x for x in r[r.index(m[0])+1:] if x)
        sheet_pub[m[0]]=(r[6] if len(r)>6 else '', who)
with open(f'{OUT}/public-ip-register.txt','w') as f:
    f.write('ATP500 public IPs 157.231.128.x (Vodafone/old WAN ge1). Device = running-config 13 Oct 2026; Sheet = "Routing-Public IP" + "NAT" tabs.\n\n')
    f.write(f"{'IP':<17}{'Device policy-route SNAT':<26}{'Device NAT / virtual server':<60}{'Sheet says':<40}\n")
    for ip in sorted(pubs, key=lambda x:int(x.split('.')[-1])):
        d=pubs[ip]; s=sheet_pub.get(d['obj'],('',''))
        f.write(f"{ip:<17}{','.join(d['policy_route']) or '-':<26}{'; '.join(d['virtual_server']) or '-':<60}{(s[0]+' '+s[1]).strip() or '-':<40}\n")

# ---------- text views ----------
def table(path, header, lines):
    with open(path,'w') as f:
        f.write(header+'\n'); f.write('\n'.join(lines)+'\n')
lines=[]
for r in reg:
    v,side,st,name,bw,pub,notes,ddesc,dip,up,leases,arps,bwd,snat,pol,ports,ten,flags=r
    lines.append(f"VLAN {v:<4} {side:<9} sheet={st or '-':<12} {name[:34]:<34} bw={str(bw) or '-':<8} dev={ddesc[:30]:<30} {up:<4} leases={leases!s:<3} arp={arps!s:<3} ports={ports or '-'}")
    if bwd: lines.append(f"          rule: {bwd}")
    if snat: lines.append(f"          SNAT: {snat}")
    if ten: lines.append(f"          sheet tenants: {ten}")
    if flags: lines.append(f"          >> {flags}")
table(f'{OUT}/vlan-register.txt','VLAN register: sheet (7 Oct 2026) vs devices (13/14 Oct 2026)', lines)
lines=[]
for row,sw,ports,cl,v,note,act in pc:
    lines.append(f"{v:<16} {row['org'][:34]:<34} {row['room'][:22]:<22} {sw or row['sw'][:10]:<10} ports={'/'.join(map(str,ports)) or '?':<14} vlan={'/'.join(map(str,cl)) or '?':<10} {act} {('['+note+']') if note else ''}")
table(f'{OUT}/port-check.txt','Config sheet switch/port claims vs switch running-configs (14 Oct 2026)', lines)
lines=[f"{sw} port {p:<3} untagged VLAN {u:<4} tagged {','.join(map(str,t)) or '-'}" for sw,p,u,t in undoc]
table(f'{OUT}/undocumented-ports.txt','Access ports carrying a tenant VLAN that no row of the config sheet claims (uplinks excluded)', lines)

# summary counts
c=collections.Counter(v for _,_,_,_,v,_,_ in pc)
print('port-check verdicts:', dict(c))
print('vlans in register:', len(reg), ' flagged:', sum(1 for r in reg if r[-1]))
print('undocumented access ports:', len(undoc))

# ---------- Bootstrap's margin notes = intent signals ----------
INTENT = [
 (r'moved to fortigate\s*(vlan\s*\d+)?', 'MOVED-TO-FORTIGATE'),
 (r'on fortigate firewall|fortigate firewall', 'ON-FORTIGATE'),
 (r'can be reused|left - can be reused|reused', 'FREE-REUSABLE'),
 (r'\bleft\b|vacated|left office|left space|cancelled internet', 'TENANT-LEFT'),
 (r'make (as )?shared|make shared', 'MAKE-SHARED'),
 (r'move nats to fortigate', 'NAT-TO-FORTIGATE'),
 (r'change when moving to vorboss', 'FIX-AT-VORBOSS-MOVE'),
 (r'needs to be separated', 'SEPARATE-TENANTS'),
 (r'nat config|possible nat', 'HAS-NAT'),
 (r'static ip', 'STATIC-IP'),
 (r'to bill|not charged|requesting more|split charges', 'BILLING'),
 (r'given to|taken over|moved to (?!fortigate)', 'REASSIGNED'),
 (r'\?\?|not sure|duplicate', 'UNCLEAR'),
 (r'keeping their old conne', 'DUAL-RUNNING'),
 (r'not needed', 'NOT-NEEDED'),
]
def classify(text):
    t=(text or '').lower(); tags=[]
    for rx,tag in INTENT:
        if re.search(rx,t) and tag not in tags: tags.append(tag)
    return tags
intent=[]
for v in all_v:
    srcs=[]
    if v in atp_sheet:
        n=atp_sheet[v]
        srcs.append(('VLANs-ATP500 tab', f"status={n['status']}; {n['notes']}".strip('; ')))
    if v in fg_sheet:
        n=fg_sheet[v]
        srcs.append(('VLANS-FORTIGATE tab', f"status={n['status']}; client={n['client']}; {n['notes']}".strip('; ')))
    for row in cfg:
        if v in {int(x) for x in re.findall(r'\d+', row['vlan'])}:
            srcs.append(('BS config sheet', f"{row['org']} [{row['room']}]: {(row['ipinfo']+' '+row['details']).strip()}"))
    tags=set()
    for s,t in srcs: tags.update(classify(t))
    if tags: intent.append((v,sorted(tags),srcs))
# other tabs' intent lines
extra=[]
for r in rows('NAT'):
    j=' '.join(r)
    if classify(j): extra.append(('NAT tab', j.strip(' |')))
for r in rows('Routing-Public_IP'):
    j=' '.join(x for x in r if x)
    if classify(j) and 'Public_IP' in j: extra.append(('Routing-Public IP tab', j))
with open(f'{OUT}/intent-notes.txt','w') as f:
    f.write("Bootstrap's margin notes, pulled out of the workbook (7 Oct 2026) and tagged. These are THEIR notes, not a plan of ours.\n"
            "Tags: MOVED-TO-FORTIGATE / ON-FORTIGATE = already migrated per sheet; FREE-REUSABLE, TENANT-LEFT = candidates to drop;\n"
            "HAS-NAT, STATIC-IP, NAT-TO-FORTIGATE = public-IP/NAT work to carry over; MAKE-SHARED, SEPARATE-TENANTS, FIX-AT-VORBOSS-MOVE = design changes they want.\n\n")
    for v,tags,srcs in intent:
        f.write(f"VLAN {v}: {', '.join(tags)}\n")
        for s,t in srcs:
            if t.strip(): f.write(f"    [{s}] {t}\n")
    f.write("\nOther tabs:\n")
    for s,t in extra: f.write(f"    [{s}] {t}\n")
with open(f'{OUT}/intent-notes.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['vlan','tags','source_tab','note'])
    for v,tags,srcs in intent:
        for s,t in srcs: w.writerow([v,';'.join(tags),s,t])
print('intent vlans:', len(intent))

# ---------- bandwidth: sheet vs device ----------
bwl=[]
for v in all_v:
    k=f'vlan{v}'
    sh=atp_sheet.get(v) or fg_sheet.get(v)
    if not sh: continue
    m=re.match(r'^\s*(\d+)', str(sh['bw']))
    sheet=int(m.group(1)) if m else None
    if k in atp_if:
        rules=re.findall(r'down=(\d+)M', '; '.join(bwm.get(k,[])))
        dev=int(rules[0]) if rules else None; src='ATP500 bwm'
    elif v in fg_if:
        dev=fg_if[v]['out'] or None; src='FortiGate outbandwidth'
    else: continue
    if sheet is None and dev is None: continue
    if sheet is not None and dev is not None and abs(sheet-dev)<=3: continue
    bwl.append(f"VLAN {v:<4} sheet={str(sheet) if sheet is not None else '-':<5} device={str(dev)+'M' if dev else 'NO RULE':<9} ({src}; {sh.get('status','')}) {str(sh['bw']) if sheet is None else ''}")
with open(f'{OUT}/bandwidth-check.txt','w') as f:
    f.write('Bandwidth: sheet column vs device rule (ATP500 bwm inbound guarantee, FortiGate interface outbandwidth). Only differences listed.\n')
    f.write('\n'.join(bwl)+'\n')
print('bandwidth differences:', len(bwl))
