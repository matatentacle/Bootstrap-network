---
name: bootstrap-miro-board
description: "Bootstrap Miro board (uXjVJ1aoEDY=) layout, which frames are current vs historical, and the 10G migration plan summary as of 14 Oct 2026"
metadata:
  node_type: memory
  type: project
  originSessionId: b6344eb6-aa50-4143-a526-eed765b70e9f
  modified: 2026-10-14T15:20:26.366Z
---

Mat's Miro board "Bootstrap" (https://miro.com/app/board/uXjVJ1aoEDY=/) is a scratch pad. Read it with the Miro canvas tools; the frame SVGs are big, so extract text with python from the saved tool result.

**Current (Oct 2026):** frame "10G migration plan" containing "Old Config" and "New Config" (the "New Plan" sticky is the source of truth). Same content as ~/jumpbox-setup/"Bootstrap - 10G migration plan.jpg". Plan: retire SW02 and the ATP500, Vorboss 10G WAN on FortiGate x4, FortiGate x1(+x2) LAG to SW101 (XS1935-12F), 8 satellite cabinets re-patched from SW01/SW02 SFP ports onto SW101 SFP 3-6 and SW102 SFP 1-5 over fibre pair 1 of the existing multimode tie lines, SW102 SFP 6 to SW01 port 25, FHG over a 4-core singlemode tie line (SC panel).

**Historical (do not mix in):** the per-cabinet frames (PH1, PH2, PH3, PHB, FH2, FH3, CW2, CW3, Main Cab) are the earlier physical clean-up notes. The "Main Cab" note about "16 fibre patch + 8 Zyxel + 8 FortiGate 1G modules" is the superseded 1G-from-FortiGate design. The embedded Google Sheet "A254 - BStrap Equipment Cost Breakdown" is the cost tracker (Cat6 patch counts per cabinet, 1 test SFP).

**Why:** Mat asked for old and new notes to be kept separate so context does not get garbled.
**How to apply:** take design facts only from the 10G migration plan frame; treat cabinet frames as history. Shopping list produced 14 Oct 2026: ~/jumpbox-setup/SHOPPING-LIST-10G-2026-10-14.txt (for Shopna, who places orders). FortiGate x1 and x4 hold generic OEM SFP-10G-SR optics, x2/x3 sit in the fortilink aggregate. See [[switch-layer]] and [[bootstrap-jumpbox]].
