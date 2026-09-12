import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote
from build_library import build


class LibraryTests(unittest.TestCase):
    def test_add_remove_nested_files_and_escape_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / 'html/하위 폴더'
            folder.mkdir(parents=True)
            book = folder / '새 책 & 질문.html'
            book.write_text('<title>Fallback</title><h1>A &amp; B &lt;script&gt;</h1>', encoding='utf-8')
            self.assertEqual(build(root), 1)
            main = (root / 'index.html').read_text(encoding='utf-8')
            local = (root / 'html/index.html').read_text(encoding='utf-8')
            self.assertIn(quote('html/하위 폴더/새 책 & 질문.html'), main)
            self.assertIn(quote('하위 폴더/새 책 & 질문.html'), local)
            self.assertIn('A &amp; B &lt;script&gt;', main)
            self.assertEqual(build(root), 1)  # Generated index must not become a book.
            book.rename(folder / 'removed.txt')
            self.assertEqual(build(root), 0)
            self.assertNotIn('A &amp; B', (root / 'index.html').read_text(encoding='utf-8'))

    def test_publish_keeps_relative_assets_and_original_texts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'repo'
            (root / 'html').mkdir(parents=True)
            (root / '원본 유튜브 요약 텍스트').mkdir()
            (root / 'html/book.htm').write_text('<title>Book</title>', encoding='utf-8')
            (root / 'html/cover.svg').write_text('<svg/>', encoding='utf-8')
            raw = root / '원본 유튜브 요약 텍스트/원본.txt'
            raw.write_bytes(b'unchanged\r\n')
            (root / 'private-build-file').write_text('not published')
            output = Path(tmp) / 'published'
            self.assertEqual(build(root, output), 1)
            self.assertEqual((output / raw.relative_to(root)).read_bytes(), raw.read_bytes())
            self.assertTrue((output / 'html/cover.svg').exists())
            self.assertTrue((output / 'index.html').exists())
            self.assertTrue((output / '.nojekyll').exists())
            self.assertFalse((output / 'private-build-file').exists())


if __name__ == '__main__':
    unittest.main()
