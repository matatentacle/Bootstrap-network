#!/usr/bin/env bash
# Run one read-only FortiOS command over SSH and save the output.
# Usage: bash ~/jumpbox-setup/fortigate-cmd.sh "<command>" <outfile>
# If the account has two-factor on (the `mat` account became super_admin + 2FA on 20 Oct 2026),
# the gateway asks for a token after the password: pass it as FGT_OTP=123456 in the environment,
# otherwise the script stops at the token prompt with exit 6 instead of hanging.
set -uo pipefail
HOST=192.168.10.99
USER_=$(awk '/^Fortinet/{f=1} f&&/^Username/{print $3; exit}' ~/jumpbox-setup/.env)
PASS_=$(awk '/^Fortinet/{f=1} f&&/^Pass/{sub(/^Pass - /,""); print; exit}' ~/jumpbox-setup/.env)
[[ -n "$USER_" && -n "$PASS_" ]] || { echo "no Fortinet credentials in ~/jumpbox-setup/.env" >&2; exit 1; }
CMD="$1"; file="$2"
export USER_ PASS_ HOST CMD FGT_OTP="${FGT_OTP:-}"
expect <<'EXP' 2>"$file.err" | sed -e 's/\r$//' -e 's/--More--//g' > "$file"
  log_user 0
  set timeout 60
  spawn ssh -o StrictHostKeyChecking=accept-new $env(USER_)@$env(HOST)
  expect {
    -re "(P|p)assword:" { send "$env(PASS_)\r" }
    timeout { puts stderr "no password prompt"; exit 2 }
  }
  expect {
    -re "(\\$|#) $" {}
    -re "(P|p)assword:" { puts stderr "login refused (password rejected)"; exit 3 }
    -re "(?i)(token|code|authenticat)\[^\r\n\]*:? ?$" {
      if {$env(FGT_OTP) eq ""} { puts stderr "gateway wants a 2FA token: set FGT_OTP=<6 digits> and rerun"; exit 6 }
      send "$env(FGT_OTP)\r"
      expect {
        -re "(\\$|#) $" {}
        timeout { puts stderr "no prompt after 2FA token"; exit 7 }
      }
    }
    timeout { puts stderr "no prompt after login"; exit 4 }
  }
  set timeout 600
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
rc=${PIPESTATUS[0]}
[ -s "$file.err" ] && cat "$file.err" >&2 || rm -f "$file.err"
echo "saved $file ($(wc -l < "$file") lines, rc=$rc, user=$USER_)"
exit $rc
