"""Read-only helper tests. Neither sync.main nor thumbs.main is invoked."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


sync = module('arcade_sync_helpers', ROOT / 'sync.py')
thumbs = module('arcade_thumbnail_helpers', ROOT / 'tools/thumbs.py')


class SiteSupport(unittest.TestCase):
    def test_zero_one_and_multiple_review_blocks(self):
        game = {'source': 'example.html', 'title': 'Example'}
        page = '<title>Example</title><a href="index.html">Arcade</a>'
        self.assertIn('Example · AI Arcade', sync.clean(page, game))
        review = '<details class="review-about"><a href="../README.md">Notes</a></details>'
        self.assertNotIn('README', sync.clean(page + review, game))
        with self.assertRaisesRegex(AssertionError, 'zero or one'):
            sync.clean(page + review + review, game)
        with self.assertRaisesRegex(AssertionError, 'leave the site'):
            sync.clean(page + '<a href="../README.md">Other link</a>', game)
        legacy = '<details class="review-about"><p id="about">Notes</p></details>'
        self.assertIn(sync.STUB, sync.clean(page + legacy, game))

    def test_registered_pages_and_terminal_clean_without_writing(self):
        for game in sync.CONFIG['games']:
            with self.subTest(slug=game['slug']):
                self.assertIn('AI Arcade', sync.clean((sync.PILOTS / game['source']).read_text(), game))
                if game.get('thumb_asset'):
                    self.assertIn('<svg', thumbs.asset_markup(game['thumb_asset'], sync.PILOTS))
        terminal = sync.PILOTS / 'transfer-desk-terminal.html'
        self.assertNotIn('review-about', sync.clean(terminal.read_text(), {'source': terminal.name, 'title': 'Transfer Desk'}))

    def test_asset_contract_and_unsafe_or_textual_assets(self):
        valid = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600"><rect width="960" height="600" fill="#123"/></svg>'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'ok.svg').write_text(valid)
            self.assertEqual(thumbs.asset_markup('ok.svg', root), valid)
            with self.assertRaisesRegex(AssertionError, 'inside pilots'):
                thumbs.asset_markup('../escape.svg', root)
            for content in ['<text>Not allowed</text>', '<script/>', '<foreignObject/>', '<image href="photo.png"/>', '<path onclick="x()"/>', '<use href="https://example.com/x.svg"/>', '<path fill="url(https://example.com/x)"/>']:
                with self.subTest(content=content):
                    (root / 'bad.svg').write_text(valid.replace('<rect width="960" height="600" fill="#123"/>', content))
                    with self.assertRaises(AssertionError):
                        thumbs.asset_markup('bad.svg', root)

    def test_asset_renderer_size_and_existing_capture_helpers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(thumbs, 'chrome', return_value=Mock(returncode=0)) as chrome, patch.object(thumbs, 'finish') as finish:
                thumbs.render_asset('<svg/>', root / 'probe.html', root / 'shot.png', root / 'out.jpg')
                self.assertIn('--window-size=1280,800', chrome.call_args.args)
                finish.assert_called_once_with(root / 'shot.png', 2560, 1600, root / 'out.jpg')
        self.assertEqual(thumbs.padded(960, 600), (600, 960))
        self.assertIn('.exb>button', thumbs.hide('#results'))
        self.assertIn('width:960px;height:600px', thumbs.asset_page('<svg/>', 960))


if __name__ == '__main__':
    unittest.main()
