AuroraBoot - Marquardt build (PRIVATE: contains the Marquardt logo, do not publish to a public repo)

1) Try it in a VM first:   sudo apt install gnu-efi gcc make qemu-system-x86 ovmf ; make run
   (make run uses config/demo.conf with fake entries; to preview the branded look use: CONF=config/mq.conf make run)
2) Real machine: read README.md > Limits. A company laptop almost always has Secure Boot on, which will refuse this
   unsigned binary, and IT policy may forbid boot changes. Ask IT first.
3) Safest real test (Linux dual-boot):  sudo install/install-linux.sh --try   (boots once, boot order unchanged)
Prebuilt branded binary: dist/AuroraBoot.efi
