#!/usr/bin/env python3
"""Headless QEMU driver: boots AuroraBoot, sends keys, saves PNG screenshots (and a GIF).
usage: tools/screenshot.py OUTDIR [--conf config/demo.conf] [--efi build/AuroraBoot.efi]"""
import argparse, glob, os, shutil, socket, subprocess, sys, time
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--conf", default="config/demo.conf")
ap.add_argument("--efi", default="build/AuroraBoot.efi"); ap.add_argument("--gif", default=""); a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
esp = "/tmp/ab_esp"; shutil.rmtree(esp, ignore_errors=True)
os.makedirs(f"{esp}/EFI/BOOT"); os.makedirs(f"{esp}/EFI/AuroraBoot")
shutil.copy(a.efi, f"{esp}/EFI/BOOT/BOOTX64.EFI"); shutil.copy(a.conf, f"{esp}/EFI/AuroraBoot/aurora.conf")
cands = [p for p in glob.glob("/usr/share/OVMF/OVMF_CODE*.fd") + glob.glob("/usr/share/edk2*/**/OVMF_CODE*.fd", recursive=True) if not any(x in p for x in ("secboot", "snakeoil", ".ms."))]
ovmf = sorted(cands, key=len)[0]   # plain firmware: Secure Boot off, so the unsigned .efi runs
sock = "/tmp/ab_mon"; 
if os.path.exists(sock): os.remove(sock)
q = subprocess.Popen(["qemu-system-x86_64", "-machine", "q35", "-m", "512", "-vga", "std", "-display", "none",
    "-drive", f"if=pflash,format=raw,readonly=on,file={ovmf}", "-drive", f"format=raw,file=fat:rw:{esp}",
    "-usb", "-device", "usb-mouse", "-monitor", f"unix:{sock},server,nowait"], stderr=subprocess.DEVNULL)
for _ in range(50):
    if os.path.exists(sock): break
    time.sleep(0.1)
s = socket.socket(socket.AF_UNIX); s.connect(sock); s.settimeout(5); time.sleep(0.3); s.recv(4096)
def cmd(c):
    s.sendall((c + "\n").encode()); time.sleep(0.05)
    try: s.recv(65536)
    except Exception: pass
n = [0]
def shot(name):
    p = f"/tmp/ab_{n[0]}.ppm"; n[0] += 1; cmd(f"screendump {p}")
    for _ in range(40):
        if os.path.exists(p) and os.path.getsize(p) > 1000: break
        time.sleep(0.05)
    time.sleep(0.05); im = Image.open(p).convert("RGB"); im.save(f"{a.out}/{name}.png"); os.remove(p); return im
frames = []
def burst(seconds, every=0.12):
    t = time.time()
    while time.time() - t < seconds:
        p = f"/tmp/ab_f{len(frames)}.ppm"; cmd(f"screendump {p}"); time.sleep(0.02)
        try: frames.append(Image.open(p).convert("RGB").copy()); os.remove(p)
        except Exception: pass
        time.sleep(every)
try:
    time.sleep(11)                      # OVMF without KVM needs ~8-10 s to reach the bootloader
    if a.gif:
        cmd("sendkey i"); burst(2.8, 0.0)
    else:
        cmd("sendkey i"); time.sleep(0.6); shot("00-intro")
    time.sleep(2.0)
    shot("01-menu-windows")
    cmd("sendkey right"); time.sleep(1.2); shot("02-menu-ubuntu")
    cmd("sendkey right"); time.sleep(1.2); shot("03-menu-fedora")
    cmd("sendkey t"); time.sleep(1.4); shot("04-theme-ember")
    cmd("sendkey t"); time.sleep(1.4); shot("05-theme-glacier")
    cmd("sendkey t"); time.sleep(1.4); shot("06-theme-neon")
    cmd("sendkey t"); time.sleep(1.4)
    cmd("sendkey end"); time.sleep(1.3); shot("07-system-items")
    cmd("sendkey home"); time.sleep(1.0)
    if not a.gif:
        cmd("sendkey ret"); time.sleep(0.5); shot("08-boot-transition")
        time.sleep(5); 
        for _ in range(6): cmd("mouse_move 60 10"); time.sleep(0.15)
        time.sleep(1.5); shot("09-mouse-hover")
    if a.gif:
        cmd("sendkey right"); burst(1.6); cmd("sendkey right"); burst(1.6); cmd("sendkey left"); burst(1.4)
        cmd("sendkey t"); burst(1.6); cmd("sendkey ret"); burst(1.6)
        w = 960; fr = [f.resize((w, int(f.height * w / f.width)), Image.LANCZOS).quantize(colors=160, dither=Image.Dither.NONE) for f in frames]
        fr[0].save(a.gif, save_all=True, append_images=fr[1:], duration=110, loop=0, optimize=True); print("gif frames:", len(fr))
finally:
    q.terminate()
print("done")
