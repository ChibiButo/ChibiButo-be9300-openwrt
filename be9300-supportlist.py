#!/usr/bin/env python3
"""Add the retail Archer BE9300 v1.0 (US) identity to the BE550 web-UI factory support list."""
import sys
path = sys.argv[1]
entry = "\t\t{product_name:Archer BE9300,product_ver:1.0.0,special_id:55530000}\\r\\n\\\n"
anchor = "\tTPLINK_SUPPORT_STRING := SupportList:\\r\\n\\\n"
s = open(path).read()
if "product_name:Archer BE9300" in s:
    print("already present"); sys.exit(0)
if s.count(anchor) != 1:
    sys.exit("anchor not found exactly once")
s = s.replace(anchor, anchor + entry)
open(path, "w").write(s)
print("added BE9300 entry")
