from paths import ROOT
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

if str(ROOT / 'launcher') not in sys.path:
    sys.path.insert(0, str(ROOT / 'launcher'))
import tlg_run as t


class ResolutionTests(unittest.TestCase):
    """resolution(): what the startup patch gets. env > output_choice > screen snapshot."""

    def resolution(self, settings, env=None):
        saved = os.environ.pop('TLG_RESOLUTION', None)
        os.environ.update(env or {})
        try:
            return t.resolution(settings)
        finally:
            if saved is None:
                os.environ.pop('TLG_RESOLUTION', None)
            else:
                os.environ['TLG_RESOLUTION'] = saved

    def test_explicit_choice_is_the_patch(self):
        self.assertEqual(self.resolution({'output_choice': '2560x1440'}), '2560x1440')
        self.assertEqual(self.resolution({'output_choice': '1280x720'}), '1280x720')

    def test_1080p_is_native(self):
        self.assertEqual(self.resolution({'output_choice': '1920x1080'}), 'native')

    def test_auto_uses_the_screen_snapshot(self):
        # The default choice: no resolution_width/height keys must not yield 'NonexNone'.
        self.assertEqual(self.resolution({'output_choice': 'auto'}), 'native')
        self.assertEqual(self.resolution({'output_choice': 'auto',
                                          'resolution_width': 2560,
                                          'resolution_height': 1440}), '2560x1440')

    def test_missing_choice_is_native(self):
        self.assertEqual(self.resolution({}), 'native')
        self.assertEqual(self.resolution({'output_choice': ''}), 'native')

    def test_env_wins(self):
        self.assertEqual(self.resolution({'output_choice': '2560x1440'},
                                         {'TLG_RESOLUTION': '1280x720'}), '1280x720')

    def test_never_returns_garbage(self):
        # The bug the review caught: formatting absent keys produced 'NonexNone'.
        for settings in ({'output_choice': 'auto'}, {'resolution_width': None},
                         {'output_choice': 'auto', 'resolution_height': None}):
            value = self.resolution(settings)
            self.assertIn(value, ('native',) + tuple(t.OUTPUT_CHOICES), settings)


class SummaryLineTests(unittest.TestCase):
    def test_parses_the_patch_summaries(self):
        self.assertEqual(t.parse_summary('Frame rate: 60 FPS mode, 4 patch writes'),
                         ('frame_rate', '60'))
        self.assertEqual(t.parse_summary('Resolution: 2560x1440, 2 patch writes'),
                         ('resolution', '2560x1440'))
        # A failed patch reports the game's own size: normalized so requested/applied agree
        # in the log header ('native', not '1920x1080').
        self.assertEqual(t.parse_summary('Resolution: 1920x1080, 0 patch writes'),
                         ('resolution', 'native'))

    def test_ignores_other_lines(self):
        for line in ('Frame rate: requested 60, applied 60',
                     'Frame rate patch flip_rate_60: 0x1c5151a ...',
                     'Resolution patch Resolution: 0x26ec3e8 ...',
                     'Mods: skipped x: y'):
            self.assertIsNone(t.parse_summary(line), line)


class PlayEnvTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # play_env reads the data folder's tlg.ini through user_dir(), which TLG_USER_DIR moves.
        patcher = mock.patch.dict(os.environ, {'TLG_USER_DIR': self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def test_never_sets_the_live_output(self):
        # TLG_OUTPUT_RES arms the artifact-prone live resample path: the startup patch owns
        # the output, so the env must never carry it.
        (self.folder / 'tlg.ini').write_text('upscaler=taa\noutput_res=2560x1440\n')
        env = t.play_env({'output_choice': '2560x1440'})
        self.assertNotIn('TLG_OUTPUT_RES', env)
        self.assertNotIn('TLG_RENDER_RES', env)  # no custom source: no compatibility session
        self.assertEqual(env.get('TLG_UPSCALER'), 'taa')

    def test_custom_source_becomes_render_res(self):
        (self.folder / 'tlg.ini').write_text('upscaler=dlss\n')
        env = t.play_env({'source_res': '1706x960'})
        self.assertEqual(env.get('TLG_RENDER_RES'), '1706x960')

    def test_untouched_ini_keeps_shell_env(self):
        # No upscaler key in the ini: build_env's default must not be overridden.
        env = t.play_env({})
        self.assertNotIn('TLG_UPSCALER', env)


if __name__ == '__main__':
    unittest.main()
