# AuroraBoot - build with:  make        (needs gcc + gnu-efi)   |  make run  (needs qemu + OVMF)
ARCH    ?= x86_64
CC      ?= gcc
EFIINC  ?= /usr/include/efi
EFILIB  ?= /usr/lib
LDS     ?= $(EFILIB)/elf_x86_64_efi.lds
CRT0    ?= $(EFILIB)/crt0-efi-x86_64.o
OVMF    ?= $(firstword $(wildcard /usr/share/OVMF/OVMF_CODE_4M.fd /usr/share/OVMF/OVMF_CODE.fd /usr/share/edk2/ovmf/OVMF_CODE.fd /usr/share/edk2-ovmf/x64/OVMF_CODE.fd))
OVMFV   ?= $(firstword $(wildcard /usr/share/OVMF/OVMF_VARS_4M.fd /usr/share/OVMF/OVMF_VARS.fd /usr/share/edk2/ovmf/OVMF_VARS.fd /usr/share/edk2-ovmf/x64/OVMF_VARS.fd))

CFLAGS  = -I$(EFIINC) -I$(EFIINC)/x86_64 -O2 -fpic -ffreestanding -fno-stack-protector -fno-stack-check \
          -fshort-wchar -mno-red-zone -maccumulate-outgoing-args -DEFI_FUNCTION_WRAPPER -Wall -Wno-unused-parameter
SRC     = src/main.c src/gfx.c src/config.c src/entries.c
OBJ     = $(SRC:.c=.o)

all: build/AuroraBoot.efi

build/AuroraBoot.efi: $(OBJ)
	@mkdir -p build
	ld -nostdlib -znocombreloc -T $(LDS) -shared -Bsymbolic -L$(EFILIB) $(CRT0) $(OBJ) -o build/AuroraBoot.so -lefi -lgnuefi
	objcopy -j .text -j .sdata -j .data -j .rodata -j .dynamic -j .dynsym -j .rel -j .rela -j '.rel.*' -j '.rela.*' -j .reloc \
	        --target efi-app-x86_64 build/AuroraBoot.so $@
	@echo "built $@ ($$(stat -c%s $@) bytes)"

src/%.o: src/%.c src/aurora.h src/gfx.h src/assets.h
	$(CC) $(CFLAGS) -c $< -o $@

# regenerate fonts/logo:  make assets LOGO=path/to/logo.png LOGO_MODE=alpha|white-on-color|dark-on-light
LOGO ?= assets/logo.png
LOGO_MODE ?= alpha
assets:
	python3 tools/gen_assets.py --logo $(LOGO) --logo-mode $(LOGO_MODE) --logo-height 300

# boot the demo in QEMU (window). Uses config/demo.conf so you see sample entries.
run: build/AuroraBoot.efi
	sh tools/run-qemu.sh

clean:
	rm -f src/*.o build/*.so build/*.efi
.PHONY: all assets run clean
