import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from reading import source_units, batches, validate, generate, render
from transcript import video_url, parse_json3, caption_candidates


class TranscriptTests(unittest.TestCase):
    def test_urls(self):
        for url in ['https://youtu.be/abcdefghijk?t=10', 'https://www.youtube.com/watch?v=abcdefghijk',
                    'https://youtube.com/shorts/abcdefghijk', 'https://youtube.com/live/abcdefghijk']:
            self.assertEqual(video_url(url)[0], 'abcdefghijk')
        for url in ['https://example.com/watch?v=abcdefghijk', 'file:///tmp/file',
                    'https://youtube.com/playlist?list=abc', 'https://youtube.com.evil.test/watch?v=abcdefghijk']:
            with self.assertRaises(ValueError):
                video_url(url)

    def test_captions_preserve_repetition_without_timestamps(self):
        self.assertEqual(parse_json3({'events': [
            {'tStartMs': 50, 'segs': [{'utf8': '안녕'}, {'utf8': '하세요'}]},
            {'segs': [{'utf8': '안녕하세요'}]}]}), '안녕하세요\n안녕하세요')
        track = {'ext': 'json3', 'url': 'https://example.test'}
        result = list(caption_candidates({'subtitles': {'ko': [track]},
                                         'automatic_captions': {'ko': [track]}}, 'ko'))
        self.assertEqual([r[0] for r in result], ['subtitles', 'automatic_captions'])


class ReadingTests(unittest.TestCase):
    def test_long_input_coverage_and_timestamps(self):
        text = '[00:01] 첫 문장입니다.\n00:02 두 번째 문장. 오후 3:30에 만납니다.\n' + '긴 문장을 보존합니다. ' * 1400
        units = source_units(text)
        self.assertTrue(all(len(u['text']) <= 800 for u in units))
        self.assertEqual(units[0]['text'], '첫 문장입니다.')
        self.assertIn('3:30', units[1]['text'])
        self.assertEqual([u for group in batches(units) for u in group], units)
        self.assertEqual(''.join(u['text'].replace(' ', '') for u in units[2:]), ('긴 문장을 보존합니다. ' * 1400).replace(' ', ''))

    def test_reject_omission_reorder_and_shortening(self):
        batch = [{'id': 1, 'text': '원문 ' * 100}, {'id': 2, 'text': '끝'}]
        for units in [[], [{'id': 2, 'text': '끝', 'chapter': ''}],
                      [{'id': 1, 'text': '요약', 'chapter': '장'}, {'id': 2, 'text': '끝', 'chapter': ''}]]:
            with self.assertRaises(ValueError):
                validate(batch, {'units': units, 'summary': '요약'})

    def test_generation_cache_and_offline_escape(self):
        result = {'units': [{'id': 1, 'text': '본문 <script>alert(1)</script> {{TITLE}}', 'chapter': '첫 장'}], 'summary': '간단한 요약'}
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(status='completed', output_text=json.dumps(result))
        with tempfile.TemporaryDirectory() as tmp:
            args = ('본문입니다.', '제목 <img>', 'https://youtube.com/watch?v=abcdefghijk', client, 'model', Path(tmp))
            doc = generate(*args, log=lambda _: None)
            self.assertEqual(doc, generate(*args, log=lambda _: None))
            self.assertEqual(client.responses.create.call_count, 1)
            page = render(doc)
        self.assertIn('&lt;script&gt;', page)
        self.assertNotIn('<img>', page)
        self.assertIn('{{TITLE}}', page)
        self.assertIn('href="#chapter-1"', page)
        self.assertNotIn('<script src=', page)
        self.assertNotIn('<link ', page)
        self.assertNotIn('<img ', page)

    def test_incomplete_api_response_is_not_cached(self):
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(status='incomplete', output_text='')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                generate('원문', '제목', 'url', client, 'model', Path(tmp), log=lambda _: None)
            self.assertEqual(list(Path(tmp).rglob('*.json')), [])


if __name__ == '__main__':
    unittest.main()
