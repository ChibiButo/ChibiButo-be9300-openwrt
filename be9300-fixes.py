#!/usr/bin/env python3
"""BE9300/BE550 fixes applied on top of openwrt PR #25470 (run from the repo root)."""
import shutil, sys, glob, os
ow = sys.argv[1]

# 5/6 GHz: the QCN6274's OTP board id is blank (board_id 0xff), so ath12k picks
# single-MAC and the firmware rejects the MAC1 WMI service (-71), leaving 6 GHz
# absent and crashing when an AP starts. Describe the split-PHY topology in DT
# and backport openwrt main's 108/109 ath12k patches that honour it.
dts = os.path.join(ow, "target/linux/qualcommbe/dts/ipq9554-archer-be550-v1.dts")
s = open(dts).read()
anchor = '\t\t\tqcom,calibration-variant = "TP-Link-Archer-BE550-v1";\n'
if "qcom,split-phy" not in s:
    if s.count(anchor) != 1:
        sys.exit("DTS anchor not found exactly once")
    s = s.replace(anchor, anchor + "\t\t\tqcom,split-phy;\n")
    open(dts, "w").write(s)
    print("DTS: added qcom,split-phy to the QCN6274 node")

dst = os.path.join(ow, "package/kernel/mac80211/patches/ath12k")
for p in sorted(glob.glob("patches/mac80211-ath12k/*.patch")):
    target = os.path.join(dst, os.path.basename(p))
    if os.path.exists(target):
        sys.exit(f"patch name collision: {target}")
    shutil.copy(p, target)
    print("mac80211: added", os.path.basename(p))
