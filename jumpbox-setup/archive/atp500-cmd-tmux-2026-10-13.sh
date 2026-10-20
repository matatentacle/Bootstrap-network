#!/usr/bin/env bash
# Run one read-only command in the existing 'atp' tmux session (already logged into the ATP500),
# page through "--More--", and save the output. Usage: atp500-cmd.sh "<command>" <outfile>
set -uo pipefail
CMD="$1"; OUT="$2"; D=$(date +%F); LOGF=/srv/configs/atp500/session-$D.log
start=$(stat -c %s "$LOGF")
tmux send-keys -t atp "$CMD" Enter
n=0
while true; do
  sleep 1; n=$((n+1))
  last=$(tmux capture-pane -t atp -p | grep -v '^$' | tail -1)
  if echo "$last" | grep -qE '^Router[>#] ?$'; then break; fi
  if echo "$last" | grep -qiE 'more'; then tmux send-keys -t atp " "; fi
  [ $n -ge 600 ] && { echo "timeout on: $CMD" >&2; break; }
done
tail -c +$((start+1)) "$LOGF" | sed -e 's/\x1b\[[0-9;]*[A-Za-z]//g' -e 's/\r//g' -e 's/--More--//g' -e '/^Router[>#] *$/d' > "$OUT"
echo "saved $OUT ($(wc -l < "$OUT") lines, ${n}s)"
