#!/usr/bin/env bash
# Read-only FortiGate discovery over SSH. Saves each command's output under /srv/configs/fortigate/.
# Usage: bash ~/jumpbox-setup/fortigate-discover.sh
set -uo pipefail
HOST=192.168.10.99
USER_=$(awk '/^Fortinet/{f=1} f&&/^Username/{print $3; exit}' ~/jumpbox-setup/.env)
PASS_=$(awk '/^Fortinet/{f=1} f&&/^Pass/{sub(/^Pass(word)? - /,""); print; exit}' ~/jumpbox-setup/.env)
OUT=/srv/configs/fortigate; D=$(date +%F); mkdir -p "$OUT"
# Each command is a separate login. If the account has 2FA, one FGT_OTP code only covers the
# first login; use a non-2FA read-only account for this script, or run fortigate-cmd.sh per command.
export USER_ PASS_ HOST FGT_OTP="${FGT_OTP:-}"

run() {  # run one FortiOS command, page through --More--, write to file
  local cmd="$1" file="$2"
  CMD="$cmd" expect <<'EXP' 2>"$file.err" | sed -e 's/\r$//' -e 's/--More--//g' > "$file"
    log_user 0
    set timeout 60
    spawn ssh -o StrictHostKeyChecking=accept-new $env(USER_)@$env(HOST)
    expect {
      -re "(P|p)assword:" { send "$env(PASS_)\r" }
      timeout { puts stderr "no password prompt"; exit 2 }
    }
    expect {
      -re "(\\$|#) $" {}
      -re "(P|p)assword:" { puts stderr "login refused"; exit 3 }
      -re "(?i)(token|code|authenticat)\[^\r\n\]*:? ?$" {
        if {$env(FGT_OTP) eq ""} { puts stderr "gateway wants a 2FA token: set FGT_OTP=<6 digits> or use a non-2FA account"; exit 6 }
        send "$env(FGT_OTP)\r"
        expect {
          -re "(\\$|#) $" {}
          timeout { puts stderr "no prompt after 2FA token"; exit 7 }
        }
      }
      timeout { puts stderr "no prompt after login"; exit 4 }
    }
    set timeout 2400
    log_user 1
    send "$env(CMD)\r"
    expect {
      -re "--More--" { send " "; exp_continue }
      -re "\r\nFW-120G-01 (\\$|#) $" {}
      timeout { puts stderr "timeout during command" }
    }
    log_user 0
    send "exit\r"
    expect eof
EXP
  local rc=$?
  [ -s "$file.err" ] && cat "$file.err" >&2 || rm -f "$file.err"
  echo "saved $file ($(wc -l < "$file") lines, rc=$rc)"
}

run "get system status"                 "$OUT/system-status-$D.txt"
run "get system interface physical"     "$OUT/interface-physical-$D.txt"
run "show system interface"             "$OUT/show-interface-$D.txt"
run "get system performance status"     "$OUT/performance-$D.txt"
run "show system admin"                 "$OUT/show-admin-$D.txt"
run "get system ha status"              "$OUT/ha-status-$D.txt"
run "get router info routing-table all" "$OUT/routing-table-$D.txt"
run "show full-configuration"           "$OUT/full-config-$D.conf"
echo "Done."
