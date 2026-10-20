#!/usr/bin/env python3
"""Import device captures into the committed tree with secrets replaced by fingerprints.

    sanitize.py import SRC DST [--force]     copy SRC -> DST, redacting secrets in text files
    sanitize.py check PATH [PATH...]         scan files/dirs for anything that looks like a secret

Why: the FortiGate runs with private-data-encryption disabled, so its "ENC" blobs are
recoverable with public tooling; the ATP500 config carries a reversible ZyMesh PSK and
admin password hashes; the Zyxel switches carry admin-password and RADIUS key lines.
None of that may reach GitHub, private repo or not. Raw captures stay in private/ (ignored).

Each secret is replaced by <REDACTED:xxxxxxxx>, the first 8 hex of its SHA-256, so two
captures can be compared ("did the admin password change?") without storing the value.

import never overwrites an existing DST file unless --force; authored files (NOTES.md,
tools) therefore keep their edits. Exit status 1 if the post-import check finds leftovers.
"""
import hashlib
import os
import re
import shutil
import sys

TEXT_EXT = {'.txt', '.conf', '.log', '.csv', '.md', '.py', '.err', '.sh', '.cfg', '.json', '.yaml', '.yml'}
BINARY_EXT = {'.xlsx', '.xls', '.jpg', '.jpeg', '.png', '.pdf', '.gif', '.zip'}
PLACEHOLDER = re.compile(r'<(REDACTED|placeholder|your-|change-?me|x+)', re.I)


def fp(secret):
    return hashlib.sha256(secret.encode('utf-8', 'surrogateescape')).hexdigest()[:8]


# Line rules: named group k is kept, s is the secret. Applied in order, all of them.
LINE_RULES = [
    ('fortios-enc', r'^(?P<k>\s*set [A-Za-z0-9_-]+ ENC )(?P<s>\S+)'),
    ('enc-blob', r'(?P<k>\bENC )(?P<s>[A-Za-z0-9+/=]{16,})'),
    ('zld-user-hash', r'^(?P<k>\s*username \S+ encrypted-password )(?P<s>\S+)'),
    ('zld-secret', r'^(?P<k>\s*(?:psk-encrypted|psk|encrypted-password|password|secret|shared-secret|'
                   r'encrypted-key|key-string|auth-key|priv-key|wep-key|encrypted-wep-key|eap-password) )(?P<s>\S+)'),
    ('zld-snmp', r'^(?P<k>\s*snmp-server (?:get-community|set-community|trap-community|community) )(?P<s>\S+)'),
    ('zynos-admin-pw', r'^(?P<k>\s*admin-password )(?P<s>.+?)\s*$'),
    ('zynos-aaa-key', r'^(?P<k>\s*aaa server key )(?P<s>.+?)\s*$'),
    ('zynos-snmp', r'^(?P<k>\s*snmp-server (?:get-community|set-community|trap-community) )(?P<s>\S+)'),
    ('zynos-aaa-server', r'^(?P<k>\s*(?:radius-server|tacacs-server) .*? key )(?P<s>\S+)'),
    ('otp-in-log', r'(?P<k>Verification code: )(?P<s>\d{4,8})'),
    ('pw-in-log', r'(?P<k>[Pp]assword: )(?P<s>\S+)'),
    ('env-pass-line', r'^(?P<k>Pass - )(?P<s>\S+)'),
]
LINE_RULES = [(n, re.compile(p)) for n, p in LINE_RULES]

PEM_RULE = re.compile(
    r'-----BEGIN (?P<t>[A-Z ]*PRIVATE KEY)-----(?P<body>.*?)-----END (?P=t)-----', re.S)

# Leftover detectors for `check`: anything matching here that is not already redacted fails.
CHECK_RULES = [
    ('private-key-block', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('enc-blob', re.compile(r'\bENC [A-Za-z0-9+/=]{16,}')),
    ('zld-user-hash', re.compile(r'encrypted-password (?!<REDACTED)\S{6,}')),
    ('zld-psk', re.compile(r'\bpsk(?:-encrypted)? (?!<REDACTED)\S{6,}')),
    ('zynos-admin-pw', re.compile(r'^\s*admin-password (?!<REDACTED)\S+', re.M)),
    ('zynos-aaa-key', re.compile(r'^\s*aaa server key (?!<REDACTED)\S+', re.M)),
    ('otp-in-log', re.compile(r'Verification code: \d{4,8}')),
    ('env-pass-line', re.compile(r'^Pass - (?!<)\S+', re.M)),
    ('aws-key', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('github-token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')),
    ('tailscale-key', re.compile(r'\btskey-[a-z]+-[A-Za-z0-9]{10,}')),
]


def redact_text(text, counts):
    def pem_sub(m):
        counts['private-key-block'] = counts.get('private-key-block', 0) + 1
        return '-----REDACTED %s fp:%s-----' % (m.group('t'), fp(m.group('body')))
    text = PEM_RULE.sub(pem_sub, text)
    out = []
    for line in text.split('\n'):
        for name, rx in LINE_RULES:
            def sub(m, name=name):
                s = m.group('s')
                if PLACEHOLDER.match(s):
                    return m.group(0)
                counts[name] = counts.get(name, 0) + 1
                return '%s<REDACTED:%s>' % (m.group('k'), fp(s))
            line = rx.sub(sub, line)
        out.append(line)
    return '\n'.join(out)


def is_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXT:
        return True
    if ext in BINARY_EXT:
        return False
    try:
        with open(path, 'rb') as f:
            chunk = f.read(4096)
        return b'\0' not in chunk
    except OSError:
        return False


def read_text(path):
    with open(path, 'r', encoding='utf-8', errors='surrogateescape', newline='') as f:
        return f.read()


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8', errors='surrogateescape', newline='') as f:
        f.write(text)


def known_env_secrets(root):
    """Plaintext values from any credentials file we can find, so check can assert they are absent."""
    vals = set()
    cands = [os.path.join(root, 'jumpbox-setup', '.env')]
    priv = os.path.join(root, 'private')
    if os.path.isdir(priv):
        cands += [os.path.join(priv, n) for n in os.listdir(priv) if n.endswith('.env')]
    for cand in cands:
        if os.path.isfile(cand):
            for line in read_text(cand).splitlines():
                m = re.match(r'^Pass - (\S+)', line)
                if m and not PLACEHOLDER.match(m.group(1)):
                    vals.add(m.group(1))
    return vals


def iter_files(paths):
    """Yields (path, display) where display is forward-slash, relative to the scanned directory."""
    for p in paths:
        if os.path.isdir(p):
            for d, dirs, files in os.walk(p):
                dirs[:] = [x for x in dirs if x not in ('.git', 'private', '__pycache__', 'node_modules')]
                for f in files:
                    full = os.path.join(d, f)
                    yield full, os.path.relpath(full, p).replace('\\', '/')
        elif os.path.isfile(p):
            yield p, p.replace('\\', '/')


def cmd_check(paths, root):
    secrets = known_env_secrets(root)
    bad = 0
    for path, shown in iter_files(paths):
        base = os.path.basename(path)
        if (base == '.env' or base.endswith('.env')) and base != '.env.example':
            print('FAIL %s: credentials file must never be committed' % shown)
            bad += 1
            continue
        if shown.endswith('bin/sanitize.py') or shown == 'sanitize.py':
            continue  # this file: its rule table would match itself
        if not is_text(path):
            continue
        try:
            text = read_text(path)
        except OSError:
            continue
        for name, rx in CHECK_RULES:
            for m in rx.finditer(text):
                line = text.count('\n', 0, m.start()) + 1
                print('FAIL %s:%d: %s' % (shown, line, name))
                bad += 1
        for s in secrets:
            if s in text:
                line = text.count('\n', 0, text.find(s)) + 1
                print('FAIL %s:%d: contains a plaintext password from the credentials file' % (shown, line))
                bad += 1
    print('check: %s' % ('FAILED, %d finding(s)' % bad if bad else 'clean'))
    return 1 if bad else 0


def cmd_import(src, dst, force, root):
    written = skipped = copied = 0
    totals = {}
    per_file = {}
    for path, rel in iter_files([src]):
        out = os.path.join(dst, rel)
        if os.path.exists(out) and not force:
            skipped += 1
            continue
        if is_text(path):
            counts = {}
            text = redact_text(read_text(path), counts)
            write_text(out, text)
            written += 1
            if counts:
                per_file[rel] = sum(counts.values())
                for k, v in counts.items():
                    totals[k] = totals.get(k, 0) + v
        else:
            os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
            shutil.copy2(path, out)
            copied += 1
    print('import: %d text files written, %d binary files copied, %d existing files left alone%s'
          % (written, copied, skipped, '' if force else ' (use --force to overwrite)'))
    if totals:
        print('redactions by rule: ' + ', '.join('%s=%d' % (k, v) for k, v in sorted(totals.items())))
        for rel, n in sorted(per_file.items(), key=lambda kv: -kv[1])[:15]:
            print('  %5d  %s' % (n, rel))
    return cmd_check([dst], root)


def main(argv):
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    if len(argv) >= 3 and argv[0] == 'import':
        force = '--force' in argv[3:]
        return cmd_import(argv[1], argv[2], force, root)
    if len(argv) >= 2 and argv[0] == 'check':
        return cmd_check(argv[1:], root)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
