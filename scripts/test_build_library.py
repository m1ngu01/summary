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

    def test_publish_contains_only_html_and_indexes(self):
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
            self.assertFalse((output / raw.relative_to(root)).exists())
            self.assertFalse((output / 'html/cover.svg').exists())
            self.assertTrue((output / 'html/book.htm').exists())
            self.assertTrue((output / 'index.html').exists())
            self.assertTrue((output / '.nojekyll').exists())
            self.assertFalse((output / 'private-build-file').exists())

    def test_empty_repository_and_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(build(root), 0)
            existing = root / 'output'
            existing.mkdir()
            (root / 'index.html').write_text('unchanged')
            with self.assertRaises(FileExistsError):
                build(root, existing)
            self.assertEqual((root / 'index.html').read_text(), 'unchanged')

    def test_title_line_break(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'html').mkdir()
            (root / 'html/book.html').write_text('<h1>First<br>Second</h1>')
            build(root)
            self.assertIn('First Second', (root / 'index.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
