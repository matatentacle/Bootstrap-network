---
name: read-only-no-permission
description: Mat has given standing permission to run any read-only command on the jump box and both gateways without asking first (given 14 Oct 2026)
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3760da2d-a63a-45f3-be4c-000e2169675e
  modified: 2026-10-14T10:40:56.319Z
---

On 14 Oct 2026 Mat said: "you don't need my permission to run any read-only commands, just go for it." This covers show/get/diagnose-style commands on the ATP500 and FortiGate and anything read-only on MINI-PC-6.

**Why:** Mat is often away from the keyboard and wants discovery to carry on unattended.
**How to apply:** Run read-only commands directly and report results. Anything that changes state on a gateway still needs a specific go-ahead; see [[gateway-working-rules]]. 2FA on the ATP500 still needs Mat to paste the code.
