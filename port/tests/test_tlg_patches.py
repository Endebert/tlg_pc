from paths import ROOT
import struct
import tempfile
import unittest
from pathlib import Path
import tlg_patches as t

TABLE = t.resolution_patches(1, 1)['resolution'][0]     # (address, original bytes, ...)


def text_with(*groups, expected=True):
    """A text segment with each patch's expected bytes (or other bytes) at its offset. A list of
    names (the old call shape) or patch-group dicts ({name: entries})."""
    if groups and isinstance(groups[0], (str, list)):
        names = groups[0] if isinstance(groups[0], list) else groups
        groups = ({name: t.PATCHES[name] for name in names},)
    text = bytearray(t.TEXT_SIZE)
    for patches in groups:
        for entries in patches.values():
            for address, original, _, _ in entries:
                offset = address - t.GHIDRA_BASE
                if offset + len(original) <= t.TEXT_SIZE:      # the mode table is in the data segment
                    text[offset:offset + len(original)] = original if expected else b'\xcc' * len(original)
    return text


def plain_elf(text):
    data = bytearray(t.TEXT_FILE_OFFSET) + text
    struct.pack_into('<16sHHIQQQIHHHHHH', data, 0,
                     b'\x7fELF\x02\x01\x01\x09', 0xfe10, 62, 1, 0, 64, 0, 0, 64, 56, 1, 0, 0, 0)
    struct.pack_into('<IIQQQQQQ', data, 64, 1, 5, t.TEXT_FILE_OFFSET, 0, 0, len(text), len(text), 0x4000)
    return data


def self_dump(text, table=None):
    """The same ELF in a SELF: one plaintext segment, stored at another file offset.
    table: bytes of a second plaintext segment of its own, holding the mode table at its address."""
    count = 2 if table is not None else 1
    base = 32 + count * 32              # segment table (count * 32), then the ELF header
    data = bytearray(0x200) + text + (table or b'')
    data[:4] = t.SELF_MAGIC
    struct.pack_into('<H', data, 24, count)
    struct.pack_into('<QQQQ', data, 32, 0x800, 0x200, len(text), len(text))
    struct.pack_into('<16sHHIQQQIHHHHHH', data, base,
                     b'\x7fELF\x02\x01\x01\x09', 0xfe10, 62, 1, 0, 64, 0, 0, 64, 56, count, 0, 0, 0)
    struct.pack_into('<IIQQQQQQ', data, base + 64, 1, 5, t.TEXT_FILE_OFFSET, 0, 0, len(text), len(text), 0x4000)
    if table is not None:
        struct.pack_into('<QQQQ', data, 64, 0x800 | (1 << 20), 0x200 + len(text), len(table), len(table))
        struct.pack_into('<IIQQQQQQ', data, base + 64 + 56, 1, 5, t.TEXT_FILE_OFFSET + len(text),
                         TABLE[0] - t.GHIDRA_BASE, 0, len(table), len(table), 0x4000)
    return data


def mode_table():
    """A data segment holding the mode table's default entry (the bytes the patch checks)."""
    return TABLE[1]


def writes_of(blob):
    """[(offset, bytes)] of every write in a patches.bin blob."""
    count, = struct.unpack_from('<Q', blob, 16)
    position, found = 24, []
    for _ in range(count):
        offset, length = struct.unpack_from('<QQ', blob, position)
        found.append((offset, blob[position + 16:position + 16 + length]))
        position += 16 + length
    return found


class FrameRatePatchTests(unittest.TestCase):
    def prepare(self, eboot, mode):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'eboot.bin').write_bytes(eboot)
            applied, lines = t.prepare(tmp, tmp, mode)
            return applied, lines, Path(tmp, 'patches.bin').read_bytes()

    def test_self_dump_of_103_gets_the_patches(self):
        # #40: a SELF dump of 1.03 has another sha256 than the plain dump, but the same code.
        applied, lines, blob = self.prepare(self_dump(text_with(t.MODES['60'])), '60')
        self.assertEqual(applied, '60')
        self.assertIn('Frame rate: 60 FPS mode, 4 patch writes', lines)
        self.assertEqual(struct.unpack_from('<8sQQ', blob), (b'G3PATCH2', 0, 4))

    def test_self_dump_of_another_build_stays_at_30(self):
        applied, lines, blob = self.prepare(self_dump(text_with(t.MODES['unlocked'], expected=False)), 'unlocked')
        self.assertEqual(applied, '30')
        self.assertEqual(struct.unpack_from('<8sQQ', blob), (b'G3PATCH2', 0, 0))

    def test_unreadable_self_stays_at_30(self):
        applied, lines, _ = self.prepare(t.SELF_MAGIC + bytes(60), '60')
        self.assertEqual(applied, '30')
        self.assertTrue(any(line.startswith('Frame rate: cannot read the SELF') for line in lines))

    def test_plain_elf_with_another_hash_stays_at_30(self):
        # Unchanged: a plain ELF is only patched when it is the checked 1.03 dump.
        applied, lines, _ = self.prepare(plain_elf(text_with(t.MODES['60'])), '60')
        self.assertEqual(applied, '30')
        self.assertTrue(any('is not v1.03' in line for line in lines))

    def test_30_writes_an_empty_patch_file(self):
        applied, lines, blob = self.prepare(b'', '30')
        self.assertEqual((applied, struct.unpack_from('<8sQQ', blob)), ('30', (b'G3PATCH2', 0, 0)))


class ModTitleIdTests(unittest.TestCase):
    EU_XML = """<?xml version="1.0"?>
<Patch>
  <TitleID><ID>CUSA03745</ID></TitleID>
  <Metadata Title="The Last Guardian" Name="Test" Author="x" PatchVer="1.0" AppVer="01.03" AppElf="eboot.bin" isEnabled="true">
    <PatchList><Line Type="bytes" Address="0x00401000" Value="90"/></PatchList>
  </Metadata>
</Patch>"""

    def test_eu_title_id_is_accepted(self):
        # The EU disc is CUSA03745 (tlg_run.py LANGUAGES_BY_TITLE); a cheat file scoped to it
        # must not be silently filtered out by TITLE_IDS.
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'eu.xml').write_text(self.EU_XML)
            found = t.mod_patches.external_patches(tmp, '01.03', t.TITLE_IDS)
            self.assertEqual([key for key, _, _ in found], ['eu.xml/Test'])


class ResolutionPatchTests(unittest.TestCase):
    def prepare(self, eboot, resolution='native', mode='30'):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'eboot.bin').write_bytes(eboot)
            applied, lines = t.prepare(tmp, tmp, mode, resolution=resolution)
            return applied, lines, Path(tmp, 'patches.bin').read_bytes()

    def build(self, resolution, table=True):
        size = t.parse_resolution(resolution) or (1, 1)
        return self.prepare(self_dump(text_with(t.resolution_patches(*size)),
                                      mode_table() if table else None), resolution)

    def test_parse_resolution(self):
        # 1920x1080 and nothing are the game's own size (no patch); a side worked out in 16:9;
        # junk and sub-64 sides are never a mode; an over-65535 side derives from the other.
        for value in ('1920x1080', 'native', '', '0x0', '1x1', '1x2x3', '63x63', 'x'):
            self.assertIsNone(t.parse_resolution(value), value)
        self.assertEqual(t.parse_resolution('99999x100'), (178, 100))
        self.assertEqual(t.parse_resolution('2560x1440'), (2560, 1440))
        self.assertEqual(t.parse_resolution('2560x0'), (2560, 1440))
        self.assertEqual(t.parse_resolution('0x1440'), (2560, 1440))
        self.assertEqual(t.parse_resolution('3840x2160'), (3840, 2160))

    def test_native_writes_no_resolution(self):
        _, lines, blob = self.build('native')
        self.assertEqual(writes_of(blob), [])
        self.assertFalse(any(line.startswith('Resolution') for line in lines))

    def test_resolution_writes_the_table_and_the_nops(self):
        _, lines, blob = self.build('2560x1440')
        found = writes_of(blob)
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0], (0x26ec3e8 - t.GHIDRA_BASE,
                                    struct.pack('<4HQ', 2560, 1440, 2560, 1440, 0)))
        self.assertEqual(found[1], (0x1c4fa6a - t.GHIDRA_BASE, b'\x90' * 23))
        self.assertIn('Resolution: 2560x1440, 2 patch writes', lines)
        # 1080p is the game's own size even when typed: no patch, but reported.
        applied, lines, blob = self.build('1920x1080')
        self.assertEqual(writes_of(blob), [])
        self.assertFalse(any(line.startswith('Resolution') for line in lines))

    def test_resolution_falls_back_when_the_bytes_differ(self):
        # Another eboot build: the mode table does not match, the patch is not applied.
        eboot = self_dump(text_with(t.resolution_patches(2560, 1440)), b'\xcc' * len(TABLE[1]))
        _, lines, blob = self.prepare(eboot, '2560x1440')
        self.assertEqual(writes_of(blob), [])
        self.assertTrue(any(line.startswith('Resolution:') and 'patch not applied' in line
                            for line in lines))
        self.assertTrue(any(line.startswith('Resolution: 1920x1080') for line in lines))

    def test_resolution_with_frame_rate_writes_both(self):
        size = t.parse_resolution('2560x1440')
        text = text_with({name: t.PATCHES[name] for name in t.MODES['60']},
                         t.resolution_patches(*size))
        _, lines, blob = self.prepare(self_dump(text, mode_table()), '2560x1440', mode='60')
        # 60 FPS: flip_rate (1 entry) + dt_snap (3 entries); resolution: table + NOPs.
        self.assertEqual(len(writes_of(blob)), 6)
        self.assertIn('Frame rate: 60 FPS mode, 4 patch writes', lines)
        self.assertIn('Resolution: 2560x1440, 2 patch writes', lines)


if __name__ == '__main__':
    unittest.main()
