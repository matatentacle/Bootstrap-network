#!/usr/bin/env bash
# Run one read-only command on a Zyxel GS1920/GS1350 switch over SSH and save the output.
# Usage: bash ~/jumpbox-setup/zyxel-sw-cmd.sh <switch-ip> "<command>" <outfile>
# Credentials: .env section "Zyxel" (Username - / Pass - lines). Nebula-managed switches: read only.
set -uo pipefail
HOST="$1"; CMD="$2"; file="$3"
USER_=$(awk '/^Zyxel/{f=1} f&&/^Username/{print $3; exit}' ~/jumpbox-setup/.env)
PASS_=$(awk '/^Zyxel/{f=1} f&&/^Pass/{sub(/^Pass - /,""); print; exit}' ~/jumpbox-setup/.env)
[[ -n "$USER_" && -n "$PASS_" ]] || { echo "no Zyxel credentials in ~/jumpbox-setup/.env" >&2; exit 1; }
export USER_ PASS_ HOST CMD TERM=vt100
expect <<'EXP' 2>"$file.err" \
  | sed -e 's/\x1b\[[0-9;]*[A-Za-z]//g' -e 's/\x1b7//g' -e 's/\r//g' -e 's/--More--//g' -e '/^[^#>]\{0,80\}[>#] *$/d' > "$file"
  log_user 0
  set timeout 120
  spawn ssh -o StrictHostKeyChecking=accept-new -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa -o KexAlgorithms=+diffie-hellman-group1-sha1,diffie-hellman-group14-sha1 -o Ciphers=+aes128-cbc,3des-cbc $env(USER_)@$env(HOST)
  expect {
    -re {(P|p)assword:} { send "$env(PASS_)\r" }
    timeout { puts stderr "no password prompt"; exit 2 }
  }
  expect {
    -re {[\r\n][^\r\n#>]{1,80}[>#] } {}
    -re {(P|p)assword:} { puts stderr "login refused"; exit 3 }
    timeout { puts stderr "no prompt after login"; exit 4 }
  }
  log_user 1
  send "$env(CMD)\r"
  expect {
    -re {--More--} { send " "; exp_continue }
    -re {[\r\n][^\r\n#>]{1,80}[>#] } {}
    timeout { puts stderr "timeout during command" }
  }
  log_user 0
  send "exit\r"
  expect eof
EXP
rc=$?
[ -s "$file.err" ] && cat "$file.err" >&2 || rm -f "$file.err"
echo "saved $file ($(wc -l < "$file") lines, rc=$rc)"
exit $rc
