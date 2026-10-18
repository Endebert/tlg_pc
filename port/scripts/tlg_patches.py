#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""The Last Guardian frame rate patches (TLG_FPS=30|60|unlocked) and community mods/cheats,
written together to out/patches.bin.

Each built-in frame rate patch is a list of {image offset, expected bytes, new bytes} for eboot
1.03 only (sha256 below, or a SELF dump of it): the expected bytes are checked in eboot.bin
before anything is written, so another build never gets byte writes in the wrong place. The
loader (probe.c apply_patches) applies the file after relocation. Image offsets are eboot
virtual addresses; the Ghidra addresses in the comments (base 0x1000000) are offset + 0x1000000.
Research: docs/60fps.md.

30 with no mods enabled writes only the boot logo skip; TLG_SKIP_INTRO=0 writes an empty patch
file and the game runs exactly as on PS4.

Mods/cheats (--mods-dir/--mods-config, mod_patches.py): shadPS4/GoldHEN cheat XML files the
player drops in the mods folder. Nothing in there has any effect until it is enabled (the
file's own isEnabled="true", or mods.json), same contract as the built-in patches above.
"""
import argparse
import hashlib
import math
import os
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mod_patches

TITLE_IDS = {'CUSA03627', 'CUSA03745'}   # US, EU (tlg_run.py LANGUAGES_BY_TITLE)
EBOOT_103_SHA256 = '91dce685be81f8f6bc88097d4fc7a62e97ca08d109621c57fe9371ae125feb3c'
SELF_MAGIC = b'O\x15=\x1d'
TEXT_FILE_OFFSET = 0x4000      # PT_LOAD 0 (R E): file offset of vaddr 0
TEXT_SIZE = 0x16b2d5c
GHIDRA_BASE = 0x1000000
# Segment types the loader maps: PT_LOAD and PT_SCE_RELRO (read-only data fixed up at load).
LOADED_SEGMENTS = (1, 0x61000010)
GAME_SIZE = (1920, 1080)       # what the game renders on a PS4 with a 1080p TV


def f32(value):
    return struct.pack('<f', value)


def rip_disp(instruction_end, target):
    """disp32 of a rip-relative operand: target - address of the next instruction (Ghidra addresses)."""
    return struct.pack('<i', target - instruction_end)


# Patches by name: [(ghidra address, expected bytes, new bytes, what it does)].
PATCHES = {
    # JsDevice/JsSwapChain init (0x1c4f9f0): sceVideoOutSetFlipRate(handle, 1) -> 0.
    # Rate 1 shows a frame every second vblank (30 Hz on the 60 Hz vblank); 0 every vblank.
    'flip_rate_60': [
        (0x1c5151a, bytes.fromhex('be01000000'), bytes.fromhex('be00000000'),
         'sceVideoOutSetFlipRate(h, 1) -> (h, 0)'),
    ],
    # Lua SetMaxFps(fps) binding (0x12091a0): game+0x180 = 1.0/fps, the engine's minimum frame
    # time. The scripts call SetMaxFps(30) (states/main.lua, common/gamesetuptbl.lua).
    # 60: load 0.5 (0x24f17e8) instead of 1.0 (0x24eaf84) -> 0.5/fps: SetMaxFps(30) means 60.
    'max_fps_double': [
        (0x12091db, bytes.fromhex('c5fa100d') + rip_disp(0x12091e3, 0x24eaf84),
         bytes.fromhex('c5fa100d') + rip_disp(0x12091e3, 0x24f17e8),
         'SetMaxFps(n): minimum frame time 1/n -> 0.5/n'),
    ],
    # Unlocked: vdivss xmm1,xmm1,xmm0 -> vxorps xmm1,xmm1,xmm1: minimum frame time 0 (no limit),
    # as SetMaxFps(0) does.
    'max_fps_off': [
        (0x12091e3, bytes.fromhex('c5f25ec8'), bytes.fromhex('c5f057c9'),
         'SetMaxFps(n): minimum frame time 1/n -> 0'),
    ],
    # SmoothDeltaTime (0x1d16480): a frame time in (0.031667, 0.035) s becomes exactly 1/30 s
    # before the 2nd-order filter and the 1/360 s rounding. These three constants are read only
    # here. 60: the same snap one octave up, (0.0158333, 0.0175) -> 1/60.
    'dt_snap_60': [
        (0x24f17f8, f32(0.035), f32(0.0175), 'dt snap upper bound 0.035 -> 0.0175'),
        (0x24f17fc, f32(1 / 30), f32(1 / 60), 'dt snap target 1/30 -> 1/60'),
        (0x24f1800, f32(0.0316666663), f32(0.0158333331), 'dt snap lower bound 0.031667 -> 0.015833'),
    ],
    # Boot logos (health warning, SIE, Japan Studio): the sequence at image 0x231d62 builds a
    # table of 0x1C-byte entries on the stack and the loop at 0x231f40 registers every entry
    # whose first dword is set (`cmp dword [rsp+rax+6F0h],0 / je`). These four `mov ...,1` are
    # those flags; with all four 0 the loop registers nothing and the ~38 s of unskippable logos
    # never play. On by default; TLG_SKIP_INTRO=0 keeps the PS4 logos.
    'skip_intro': [
        (0x1231d79, bytes.fromhex('c78424f006000001000000'),
         bytes.fromhex('c78424f006000000000000'), 'logo entry 0 (health warning) enabled -> 0'),
        (0x1231df4, bytes.fromhex('c784242807000001000000'),
         bytes.fromhex('c784242807000000000000'), 'logo entry 2 (SIE) enabled -> 0'),
        (0x1231e45, bytes.fromhex('c784244407000001000000'),
         bytes.fromhex('c784244407000000000000'), 'logo entry 3 (Japan Studio) enabled -> 0'),
        (0x1231f16, bytes.fromhex('c784240c07000001000000'),
         bytes.fromhex('c784240c07000000000000'), 'conditional enable of logo entry 1 -> 0'),
    ],
}

MODES = {
    '30': [],
    # max_fps_double/max_fps_off are left out: 60 and unlocked were reached without them
    # (game+0x180 is no frame limiter in the tested scenes; its reader is not found yet).
    # TLG_FPS_PATCHES=flip_rate_60,max_fps_off tries them.
    '60': ['flip_rate_60', 'dt_snap_60'],
    'unlocked': ['flip_rate_60'],
}
# The engine rate each mode presents at most (TLG_ENGINE_FPS: the overlay's frame limiter and
# tlg_graphics.h PresentLimit). Unlocked is paced by the present thread (TLG_VBLANK_HZ=0).
ENGINE_FPS = {'30': 30, '60': 60, 'unlocked': 240}


def parse_number(value):
    """A non-negative number (text or number, a comma may be the decimal point) rounded to the
    nearest integer; None when it is not one."""
    try:
        number = float(str(value).strip().replace(',', '.'))
    except ValueError:
        return None
    return round(number) if math.isfinite(number) and number >= 0 else None


def parse_resolution(value):
    """(width, height) of \"WxH\" (digits only, one optional 'x'); a side that is 0, empty or
    missing (or over 65535, what the game's u16 holds) is worked out from the other one in
    16:9. None, the game's own, when neither is a size, when it is the game's own size, or
    when a side is below 64 (a display size, not a mode)."""
    sides = re.fullmatch(r'(\d*)x(\d*)', str(value or '').strip().lower().replace(' ', ''))
    width, height = ((side if side and side <= 0xffff else None)
                     for side in (parse_number(text) for text in (sides.groups() if sides else ('', ''))))
    if width and not height:
        height = round(width * 9 / 16)
    elif height and not width:
        width = round(height * 16 / 9)
    return (width, height) if width and height and min(width, height) >= 64 \
        and (width, height) != GAME_SIZE and width <= 0xffff and height <= 0xffff else None


def resolution_patches(width, height):
    """{name: entries} of a resolution. The mode table (0x18 bytes per entry: u16 render W,H,
    output W,H; u64 checkerboard; name pointer) starts with the Pro list's default entry at
    0x26ec3e8: 1680x1890 checkerboard, output 3360x1890; it becomes WxH, WxH, no checkerboard.
    The 23 bytes at 0x1c4fa6a in JsDevice::CreateDevice (0x1c4f9f0) are `jne +0x167;
    cmp dword [rsp+0x124], 0x438; jbe +0x156`, the output height > 1080 test that picks the Pro
    list: NOPed, the Pro list is always used."""
    return {'resolution': [
        (0x26ec3e8, bytes.fromhex('90066207200d62070100000000000000'),
         struct.pack('<4HQ', width, height, width, height, 0),
         f'default mode 1680x1890 checkerboard -> {width}x{height}'),
        (0x1c4fa6a, bytes.fromhex('0f856701000081bc2424010000380400000f8656010000'), b'\x90' * 23,
         'CreateDevice: always use the Pro mode list'),
    ]}


def file_offset(eboot, offset, length):
    """File offset of image bytes [offset, offset + length): text by TEXT_FILE_OFFSET, anything
    after it (the data tables) through the ELF's PT_LOAD and PT_SCE_RELRO headers; None when no
    segment holds them."""
    if 0 <= offset and offset + length <= TEXT_SIZE:
        return TEXT_FILE_OFFSET + offset
    if eboot[:4] != b'\x7fELF' or len(eboot) < 0x40:
        return None
    phoff, = struct.unpack_from('<Q', eboot, 0x20)
    phentsize, phnum = struct.unpack_from('<HH', eboot, 0x36)
    for i in range(phnum):
        position = phoff + i * phentsize
        if position + 56 > len(eboot):
            break
        kind, _, p_offset, vaddr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', eboot, position)
        if kind in LOADED_SEGMENTS and vaddr <= offset and offset + length <= vaddr + filesz \
                and p_offset + offset - vaddr + length <= len(eboot):
            return p_offset + offset - vaddr
    return None


def normalize_mode(value):
    value = (value or '30').strip().lower()
    return {'unlimited': 'unlocked', 'uncapped': 'unlocked', 'free': 'unlocked', '0': 'unlocked'}.get(value, value)


def mode_writes(eboot, names):
    """[(image offset, new bytes, description)] for named PATCHES groups, after checking every
    expected byte in eboot."""
    return [write for name in names for write in writes_for(eboot, name, PATCHES[name])]


def writes_for(eboot, group, entries):
    """[(image offset, new bytes, description)] for explicit (address, expected, new, what)
    entries, after checking every expected byte in eboot. Addresses past the text segment (the
    resolution mode table) are located through the ELF's loadable segments."""
    writes = []
    for address, expected, new, what in entries:
        offset = address - GHIDRA_BASE
        if len(expected) != len(new):
            raise ValueError(f'{group}: bad patch entry at {address:#x}')
        start = file_offset(eboot, offset, len(expected))
        if start is None:
            raise ValueError(f'{group}: {address:#x} is not in the eboot image')
        found = eboot[start:start + len(expected)]
        if found != expected:
            raise ValueError(f'{group}: {address:#x} has {found.hex()}, expected {expected.hex()}')
        writes.append((offset, new, f'{group}: {address:#x} {what}'))
    return writes


def write_patch_file(path, writes):
    """G3PATCH2 (probe.c apply_patches): base 0 (no pointer slots), then (offset, length, bytes).
    Base 0 only matters for a write that lands exactly on a relocated pointer slot (none of the
    built-in frame rate patches or typical shadPS4/GoldHEN literal-value mods do); it does not
    change plain byte/float writes either way."""
    blob = struct.pack('<8sQQ', b'G3PATCH2', 0, len(writes))
    for offset, data, _ in writes:
        blob += struct.pack('<QQ', offset, len(data)) + data
    Path(path).write_bytes(blob)


def read_eboot_elf(game_dir):
    """eboot.bin as a plain ELF, unwrapping a SELF dump of any game version; None if unreadable
    or an unparsable SELF. Independent of the v1.03 pin below: mods filter by their own AppVer."""
    try:
        eboot = (Path(game_dir) / 'eboot.bin').read_bytes()
    except OSError:
        return None
    if eboot[:4] == SELF_MAGIC:
        try:
            from prepare import parse_self
            return bytes(parse_self(eboot)[0])
        except ValueError:
            return None
    return eboot


def compile_mods(game_dir, eboot, mods_dir, mods_config, lines):
    """[(offset, bytes, description)] from the player's mods folder, or [] when mods_dir is not
    set, the eboot could not be read, or nothing in there is enabled."""
    if not mods_dir or not eboot:
        return []
    try:
        segments = mod_patches.eboot_segments(eboot)
        app_version = mod_patches.game_app_version(game_dir)
        found = mod_patches.external_patches(mods_dir, app_version, TITLE_IDS)
        selected = mod_patches.external_selection(found, mods_config)
        return mod_patches.compile_external(selected, segments)
    except (OSError, ValueError, struct.error) as error:
        lines.append(f'Mods: {error}: not applied')
        return []


def prepare(game_dir, out_dir, mode, mods_dir=None, mods_config=None, resolution='native'):
    """Writes out/patches.bin for the mode, the resolution and any enabled mod; returns
    (applied mode, lines). Any problem with the frame rate patches (other eboot build,
    unexpected bytes) falls back to 30 FPS without them; a resolution problem falls back to the
    game's own 1920x1080; a mod problem only drops that mod, never the built-in patches."""
    mode = normalize_mode(mode)
    lines = []
    if mode not in MODES:
        lines.append(f'Frame rate: unknown TLG_FPS={mode!r}; using 30')
        mode = '30'
    fps_writes = []
    size = parse_resolution(resolution)
    requested_size = size is not None
    res_writes = []
    # TLG_SKIP_INTRO=0 turns the boot logo skip off; anything else (the default) applies it.
    skip = os.environ.get('TLG_SKIP_INTRO', '1') != '0'
    skip_writes = []
    eboot = None
    # TLG_FPS_PATCHES="a,b" (measurements): these patches instead of the mode's own.
    names = [n for n in os.environ.get('TLG_FPS_PATCHES', '').split(',') if n in PATCHES] or MODES[mode]
    if names or size or skip:
        first = ('Frame rate' if names else 'Skip intro' if skip else 'Resolution')  # who needs the eboot for a message
        try:
            eboot = (Path(game_dir) / 'eboot.bin').read_bytes()
        except OSError as error:
            eboot = b''
            lines.append(f'{first}: cannot read eboot.bin ({error})')
        digest = hashlib.sha256(eboot).hexdigest()
        usable = digest == EBOOT_103_SHA256
        if not usable and eboot[:4] == SELF_MAGIC:
            # A SELF dump of 1.03 (sha256 b7f61057…, #40) wraps the same ELF as the plain
            # dump the hash is for, at other file offsets: patch the ELF inside (the image
            # prepare.py hands the loader). mode_writes checks every expected byte, so a SELF
            # of another build still falls back to 30.
            try:
                from prepare import parse_self
                eboot = bytes(parse_self(eboot)[0])
                usable = True
                lines.append(f'{first}: eboot.bin is a SELF ({digest[:16]}…), checking the ELF inside')
            except ValueError as error:
                lines.append(f'{first}: cannot read the SELF eboot.bin ({error})')
        if not usable:
            if names:
                lines.append(f'Frame rate: eboot.bin is not v1.03 ({digest[:16]}…): {mode} FPS patches not applied, 30 FPS')
                mode = '30'
            if size:
                lines.append(f'Resolution: eboot.bin is not v1.03 ({digest[:16]}…): patch not applied, {GAME_SIZE[0]}x{GAME_SIZE[1]}')
                size = None
            if skip:
                lines.append(f'Skip intro: eboot.bin is not v1.03 ({digest[:16]}…): not applied')
                skip = False
        else:
            if names:
                try:
                    fps_writes = mode_writes(eboot, names)
                except ValueError as error:
                    lines.append(f'Frame rate: {error}: patches not applied, 30 FPS')
                    mode, fps_writes = '30', []
            if size:
                try:
                    res_writes = writes_for(eboot, 'Resolution', resolution_patches(*size)['resolution'])
                except ValueError as error:
                    lines.append(f'Resolution: {error}: patch not applied, {GAME_SIZE[0]}x{GAME_SIZE[1]}')
                    size = None
            if skip:
                try:
                    skip_writes = writes_for(eboot, 'Skip intro', PATCHES['skip_intro'])
                except ValueError as error:
                    lines.append(f'Skip intro: {error}: not applied')
                    skip = False
    for _, data, what in fps_writes:
        lines.append(f'Frame rate patch {what} ({data.hex()})')
    for _, data, what in res_writes:
        lines.append(f'Resolution patch {what} ({data.hex()})')
    for _, data, what in skip_writes:
        lines.append(f'Skip intro patch {what} ({data.hex()})')
    mod_writes = []
    if mods_dir:
        mod_writes = compile_mods(game_dir, eboot or read_eboot_elf(game_dir), mods_dir, mods_config, lines)
        for _, data, what in mod_writes:
            lines.append(f'Mod {what} ({data.hex()})')
    writes = fps_writes + res_writes + skip_writes + mod_writes
    write_patch_file(Path(out_dir) / 'patches.bin', writes)
    lines.append(f'Frame rate: {mode} FPS mode, {len(fps_writes + mod_writes)} patch writes')
    if skip:
        lines.append(f'Skip intro: applied, {len(skip_writes)} patch writes')
    if requested_size:
        applied = f'{size[0]}x{size[1]}' if size else f'{GAME_SIZE[0]}x{GAME_SIZE[1]}'
        lines.append(f'Resolution: {applied}, {len(res_writes)} patch writes')
    return mode, lines


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('game_dir')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--mode', default='30', help='30, 60 or unlocked')
    p.add_argument('--mods-dir', help='folder of shadPS4/GoldHEN cheat XML files')
    p.add_argument('--mods-config', help='mods.json: {"enabled": [...], "disabled": [...]}')
    p.add_argument('--resolution', default='native',
                   help="WxH; a side that is 0 is worked out in 16:9, both 0 or 1920x1080: the game's own")
    a = p.parse_args()
    _, lines = prepare(a.game_dir, a.out, a.mode, a.mods_dir, a.mods_config, a.resolution)
    print('\n'.join(lines))


if __name__ == '__main__':
    sys.exit(main())
