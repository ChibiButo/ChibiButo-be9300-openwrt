# OpenWrt for TP-Link Archer BE9300 v1 (= Archer BE550 v1)

This repo builds **OpenWrt PR [#25470](https://github.com/openwrt/openwrt/pull/25470)**
(trickpattyFH20, on top of Alexandru Gagniuc's BE550 work), pinned to commit
`5ca36819` exactly as its author tested it. One thing is added: the **TP-Link-signed
5/6 GHz firmware** the PR says has to be supplied out of tree.

Status: the PR's author reports everything working on stock **1.2.4**: all five
2.5G ports, all three Wi-Fi bands, NAND, USB, the LED bar, buttons, and dual-slot
sysupgrade. This repo's particular combination has **not been tested on hardware
yet**. The PR is an unmerged draft.

## What gets built (Actions artifact `be9300-openwrt`)

| File | Use |
|---|---|
| `*-squashfs-web-ui-factory.bin` | Install from the **stock TP-Link web UI**. No serial needed |
| `*-initramfs-uImage.itb` | RAM-boot over serial/TFTP (test without writing flash) |
| `*-squashfs-sysupgrade.bin` | Upgrades once OpenWrt is installed |

### The added firmware
The 5/6 GHz chip (QCN6274 per the PR; the GPL names it QCN9224) rejects the stock
linux-firmware image (`BHI error 0xef0a0002`) because it only accepts TP-Link-signed
firmware. The build fetches the TP-Link-signed container published for the
Archer BE800 port ([#20373](https://github.com/openwrt/openwrt/pull/20373)) from
`sidhantgoel/firmware_qca-wireless` @ `c7b7a97`. It checks the MD5
(`75754823…`) and installs it as `/lib/firmware/ath12k/QCN9274/hw2.0/firmware-2.bin`.
The container holds AMSS, dual-MAC AMSS (the mode one radio needs to serve both 5 and
6 GHz) and M3 images. The blob is fetched at build time and isn't stored in this repo.

Board data for both radios comes from upstream `firmware_qca-wireless`
(`ipq-wifi-tplink_archer-be550-v1`).

## Install option A: web UI (no serial), as tested by the PR author

1. Make sure you can get back to stock: download the official 1.2.4 firmware from
   TP-Link, and know how to reach recovery mode (hold reset while powering on, then
   browse to http://192.168.0.1).
2. Stock UI → **Advanced → System → Firmware Update** → upload
   `…-squashfs-web-ui-factory.bin` → Upgrade.
3. The stock firmware writes OpenWrt to its **inactive** slot and reboots. OpenWrt
   comes up at **http://192.168.1.1** (LuCI; set a root password first).
4. Enable Wi-Fi under Network → Wireless. Radios are off by default.

Safety nets: the stock image stays in the other slot. If the selected slot fails to
load, TP-Link's U-Boot tries the other one, and the reset-button recovery page
accepts an official signed image.
**Note:** your *first* sysupgrade from inside OpenWrt writes over the slot that
held stock. After that, recovery means the TP-Link recovery page (or serial).

## Install option B: serial RAM-boot first (most cautious)

UART is header **JP1**, 3.3 V, 115200 8N1. **Do not connect VCC.**
1. Stop autoboot (press any key within 1 s) → `IPQ9574#`
2. Run `is_sec_boot_enabled` and note the output.
3. Then:
   ```
   setenv ipaddr 192.168.1.1
   setenv serverip 192.168.1.2
   tftpboot 0x50000000 openwrt-qualcommbe-ipq95xx-tplink_archer-be550-v1-initramfs-uImage.itb
   bootm 0x50000000
   ```
   Nothing is written to flash, so a power-cycle returns to stock.
4. If everything works and you want to keep it, run `sysupgrade -n …-squashfs-sysupgrade.bin`
   from the RAM-booted system.

To revert from serial: `setenv tp_boot_idx; saveenv; reset` selects the other slot.

## What to report back
`dmesg`, `logread | grep -i -E 'ath11k|ath12k|wcss|qca8084'`, `iw dev`, `lspci`,
`cat /proc/mtd`, and which bands and ports work.

## Credits
Patrick Lawler / trickpattyFH20 (PR #25470), Alexandru Gagniuc (mrnuke; BE550 port,
IPQ9574 WCSS/ath11k), Sidhant Goel (BE800 port + firmware container), Satoshi
Ikeuchi, and the OpenWrt qualcommbe maintainers.
