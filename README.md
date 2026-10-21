# OpenWrt for TP-Link Archer BE9300 v1 (= Archer BE550 v1 board): 2.4 GHz test build

**Status: builds in CI. UNTESTED on hardware.** This is a *RAM-boot (initramfs)
image only*. It never writes to flash. Pulling power returns the router to
stock firmware.

The goal of this first image is to answer four questions in a single serial session:
1. Can U-Boot boot an unsigned image at all (`is_sec_boot_enabled`)?
2. Does the kernel boot on this board?
3. Does the integrated **2.4 GHz** radio come up (ath11k + secure WCSS)?
4. Do the wired ports come up (QCA8084 LAN, QCA8081 WAN)?

5 GHz and 6 GHz are **intentionally off** in this image. They live on one QCN9224
(split-PHY) and need the separate ath12k work. The QCN9224 is still enumerated
on PCIe2, so `lspci` will show whether it's alive.

## What's in here

| Path | What |
|---|---|
| `patches/0001-*.patch` | One OpenWrt commit, applied on top of openwrt `a31dd90f69` (main, 2026-10-21) |
| `files/` | Image overlay: BDFs + first-boot Wi-Fi test config |
| `be9300.diffconfig` | Build config seed |
| `bdf/` | TP-Link's board data from the GPL tarball (`bdwlan.b20` = 2.4 GHz, `bdwlan.b1006` = QCN9224) + the board-2.bin recipe |
| `.github/workflows/build.yml` | CI build. Images appear as the `be9300-openwrt-initramfs` artifact |

### The OpenWrt patch adds
- **`ipq9554-tplink-archer-be550-v1.dts`**: mrnuke's WIP BE550 DTS ported to current
  bindings and cross-checked against TP-Link's GPL board DTS:
  - QCA8084 quad 2.5G PHY on UNIPHY0, 10G-QXGMII, MDIO 1–4 (stock `switch_mac_mode 0x15`)
  - QCA8081 2.5G WAN on UNIPHY2, MDIO 12 (same arrangement as the merged Linksys LN6001)
  - gpio60 → LAN PHY chip reset, gpio36 → WAN PHY reset (per TP-Link/QCA reference)
  - SPI-NAND on QPIC with the SMEM partition table
  - integrated radio (`wifi0`) + secure WCSS remoteproc enabled
  - PCIe2 (QCN9224) enumerated only
- **ath11k fix (`954-…max_tx_ring`)**: the merged IPQ9574 ath11k support leaves
  `max_tx_ring = 0`, and `ath11k_dp_tx()` does `ring_selector % max_tx_ring`. That's a
  divide-by-zero on the first transmitted frame, matching the forum-reported panic
  when a client connects.
- kernel config: `IPQ_NSSCC_QCA8K`, `SPI_QPIC_SNAND`, `MTD_SPI_NAND`
- 2.4 GHz caldata loader: `0:ART` @ `0x1000`, size `0x20000` (offset from TP-Link's `/sbin/is_cal`)

### Board data
`board-2.bin` wraps TP-Link's `bdwlan.b20` (board-id 0x20) under several lookup names.
`board.bin` is the raw BDF, which ath11k falls back to if no name matches.

## What was checked, and what wasn't

Checked (no hardware needed):
- Radio layout from the GPL: integrated = 2.4 GHz (`BAND_NAME_2g=wifi0`), one QCN9224 = 5 + 6 GHz
- The DTS preprocesses against the patched v6.18 headers and parses. All labels and
  QCA8K/NSS macros resolve.
- The patch `git am`s cleanly onto the pinned base. Shell scripts pass `sh -n`.
- The `max_tx_ring` bug was confirmed against the v6.18 ath11k source.

**Not verified. These are the likely failure points, in rough order:**
1. Secure boot. If the fuse is blown, U-Boot refuses unsigned images, and nothing here helps.
2. QCA8084 clocking (the fixed 312.5 MHz / 50 MHz clock assumptions) and the reset GPIO
   mapping. LAN ports may not link. The 2.4 GHz AP exists so you still have a way in.
3. ath11k chip-id / board-name match. Mitigated by the `board.bin` fallback.
4. `0:ART` naming and the 2.4 GHz cal size.
5. The clock tree (`xo_clk` 24 MHz), taken from mrnuke's measurements on his BE550.

## How to test (needs a 3.3 V USB-UART; 115200 8N1)

1. Download the `be9300-openwrt-initramfs` artifact from the latest Actions run.
   Use `*-tplink_archer-be550-v1-initramfs-uImage.itb`.
2. Put it on a TFTP server, e.g. your PC at `192.168.0.2`, with the PC wired to a LAN port.
3. Power on, and press a key within 1 s to stop U-Boot. Then run:
   ```
   is_sec_boot_enabled
   ```
   **Copy the output.** If it says secure boot is enabled, stop here and power-cycle.
4. If it's not enabled:
   ```
   setenv ipaddr 192.168.0.1
   setenv serverip 192.168.0.2
   tftpboot 0x50000000 openwrt-qualcommbe-ipq95xx-tplink_archer-be550-v1-initramfs-uImage.itb
   bootm 0x50000000
   ```
   (Nothing is written to flash. `saveenv` is never needed.)
5. Watch the console. About a minute after boot it prints
   `*** BE9300 test Wi-Fi: SSID OpenWrt-BE9300-test  key … ***`. The key is
   generated on the router. It isn't in this public repo.
6. Capture and share:
   ```
   dmesg
   cat /proc/mtd
   lspci
   iw dev; logread | grep -i -E 'ath11k|wcss|remoteproc|be9300|qca8084|ppe'
   ip link
   ```
   Then try joining `OpenWrt-BE9300-test` from a phone and pinging 192.168.1.1.
   OpenWrt's LAN is 192.168.1.1, not TP-Link's 192.168.0.1.

To get back to stock, power-cycle.

## Credits
Alexandru Gagniuc (BE550 WIP DTS, IPQ9574 ath11k), Satoshi Ikeuchi (secure WCSS,
ath11k DT, LN6001), the OpenWrt qualcommbe maintainers, and TP-Link's GPL release.
