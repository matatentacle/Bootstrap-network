#!/usr/bin/env bash
# Run one ZLD command on the ATP500 over SSH and save the output.
# Usage: bash ~/jumpbox-setup/atp500-cmd.sh [--admin] "<command>" <outfile>
#   default : the limited-admin account (.env section "APT500" under the read-only header). Read-only, no 2FA.
#   --admin : the full-admin account (.env "APT500" section under "Full Admin accounts"). Prompt is Router#.
#             If the gateway asks for a Google Authenticator code, pass it as ATP_OTP=123456 in the environment;
#             without one the script stops at the code prompt and reports it.
# Pages through --More--, strips the echo and prompts. Replaces the tmux-session version
# (archive/atp500-cmd-tmux-2026-10-13.sh) that needed Mat to type the code into a shared session.
set -uo pipefail
HOST=192.168.254.1
SECTION='/^APT500/{f=1}'
if [[ "${1:-}" == "--admin" ]]; then SECTION='/^Full Admin/{a=1} a&&/^APT500/{f=1}'; shift; fi
USER_=$(awk "$SECTION"' f&&/^Username/{print $3; exit}' ~/jumpbox-setup/.env)
PASS_=$(awk "$SECTION"' f&&/^Pass/{sub(/^Pass - /,""); print; exit}' ~/jumpbox-setup/.env)
[[ -n "$USER_" && -n "$PASS_" ]] || { echo "no credentials found in ~/jumpbox-setup/.env" >&2; exit 1; }
CMD="$1"; file="$2"
export USER_ PASS_ HOST CMD TERM=vt100 ATP_OTP="${ATP_OTP:-}"
expect <<'EXP' 2>"$file.err" \
  | sed -e 's/\x1b\[[0-9;]*[A-Za-z]//g' -e 's/\r//g' -e 's/--More--//g' -e '/^Router[>#] *$/d' -e '1{/^Router[>#] /d}' > "$file"
  log_user 0
  set timeout 600
  spawn ssh -o StrictHostKeyChecking=accept-new $env(USER_)@$env(HOST)
  expect {
    -re {(P|p)assword:} { send "$env(PASS_)\r" }
    timeout { puts stderr "no password prompt"; exit 2 }
  }
  expect {
    -re {\r?\n\r?Router[>#] ?$} {}
    -re {(P|p)assword:} { puts stderr "login refused (password rejected)"; exit 3 }
    -re {(?i)(code|authenticat|verification|otp)[^\r\n]*:? ?$} {
      if {$env(ATP_OTP) eq ""} { puts stderr "gateway wants a 2FA code: set ATP_OTP=<6 digits> and rerun"; exit 6 }
      send "$env(ATP_OTP)\r"
      expect {
        -re {\r?\n\r?Router[>#] ?$} {}
        timeout { puts stderr "no prompt after 2FA code"; exit 7 }
      }
    }
    timeout { puts stderr "no prompt after login"; exit 4 }
  }
  log_user 1
  send "$env(CMD)\r"
  expect {
    -re {--More--} { send " "; exp_continue }
    -re {\r?\n\r?Router[>#] ?$} {}
    timeout { puts stderr "timeout during command" }
  }
  log_user 0
  send "exit\r"
  expect eof
EXP
rc=$?
[ -s "$file.err" ] && cat "$file.err" >&2 || rm -f "$file.err"
echo "saved $file ($(wc -l < "$file") lines, rc=$rc, user=$USER_)"
exit $rc
